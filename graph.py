import os
import time
from datetime import date, timedelta
from typing import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.weather import get_weather
from tools.places import get_places
from tools.routing import get_route
from tools.search import search_web
from tools.cost import estimate_cost

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model=os.getenv("LLM_MODEL"),
    temperature=0,
    timeout=120,
    max_retries=2,
)

MAX_REPLANS = 2
MAX_RESEARCH_RETRIES = 1

# Jin jagahon ka naam geocoder ko ghalat jagah le jata hai, unka asli town
ALIASES = {
    "hunza": "Karimabad",
}

def call_llm(runnable, prompt, tries=3):
    """Call the LLM and retry on network errors (but not on quota errors)."""
    for attempt in range(1, tries + 1):
        try:
            return runnable.invoke(prompt)
        except Exception as e:
            text = str(e)
            if "429" in text or "RESOURCE_EXHAUSTED" in text:
                raise
            if attempt == tries:
                raise
            print(f"LLM call failed ({type(e).__name__}), "
                  f"retry {attempt}/{tries - 1}...")
            time.sleep(2 * attempt)

def compact_research(research):
    """Shrink research data so the LLM prompt stays small."""
    out = {}
    for key in ["attractions", "restaurants", "hotels"]:
        item = research.get(key, {})
        if item.get("status") == "ok":
            out[key] = [p["name"] for p in item["places"]]
        else:
            out[key] = f"unavailable: {item.get('message', 'no data')}"

    weather = research.get("weather", {})
    out["weather"] = (weather["days"] if weather.get("status") == "ok"
                      else f"unavailable: {weather.get('message', 'no data')}")

    info = research.get("info", {})
    out["price_info"] = (info.get("answer") or "none") \
        if info.get("status") == "ok" else "unavailable"

    routes = research.get("routes", {})
    if routes.get("status") == "ok":
        out["routes_from_center"] = [
            {"to": r["to"], "driving_km": r["driving_km"],
             "driving_min": r["driving_minutes"]}
            for r in routes["legs"]
        ]
    out["note"] = research.get("city_used", {}).get("note", "")
    return out


# ---------- Schemas: LLM ke output ka format ----------
class TripRequest(BaseModel):
    destination: str
    days: int
    budget_pkr: int
    travelers: int = 1
    start_date: str = Field(default="", description="YYYY-MM-DD or empty")


class DayPlan(BaseModel):
    day: int
    activities: list[str] = Field(description="Place names from the research data")
    reason: str = Field(description="Why these places: budget, distance, weather")


class TripPlan(BaseModel):
    hotel_name: str
    hotel_per_night: int = Field(description="PKR per room per night")
    transport_total: int = Field(description="PKR for the whole trip, all travelers")
    food_per_person_per_day: int = Field(description="PKR")
    activities_total: int = Field(description="PKR entry fees etc, whole trip")
    days: list[DayPlan]
    cost_reasoning: str = Field(description="How the cost numbers were chosen")


# ---------- State: graph ki shared yaaddasht ----------
class AgentState(TypedDict, total=False):
    request: str
    trip: dict
    research: dict
    plan: dict
    cost: dict
    feedback: str
    replans: int
    research_retries: int
    decision: str
    warnings: list
    final: str


# ---------- Node 1: parse ----------
def parse_node(state: AgentState):
    """Extract destination, days, budget and travelers from the user's text."""
    parser = llm.with_structured_output(TripRequest)
    trip = call_llm(
        parser,
        "Extract trip details from this request. Leave start_date empty "
        f"if not mentioned.\n\n{state['request']}",
    )
    return {
        "trip": trip.model_dump(),
        "replans": 0,
        "research_retries": 0,
        "warnings": [],
        "research": {},
    }


# ---------- Node 2: research ----------
def research_node(state: AgentState):
    """Call Places, Weather, Search and Routing tools."""
    trip = state["trip"]
    city = trip["destination"]
    start = trip["start_date"] or str(date.today() + timedelta(days=7))
    end = str(date.fromisoformat(start) + timedelta(days=trip["days"] - 1))

    old = state.get("research", {})
    res = dict(old)

    def needed(key):
        return key not in old or old[key].get("status") != "ok"

    search_city = old.get("city_used", {}).get("name") or city
    note = old.get("city_used", {}).get("note", "")

    if needed("attractions"):
        res["attractions"] = get_places.invoke(
            {"city": search_city, "category": "attractions", "limit": 8})
        alias = ALIASES.get(city.lower())
        if res["attractions"].get("status") != "ok" and alias \
                and alias != search_city:
            search_city = alias
            note = (f"'{city}' returned no places, so '{alias}' "
                    "(the main town) was used instead.")
            res["attractions"] = get_places.invoke(
                {"city": search_city, "category": "attractions", "limit": 8})

    res["city_used"] = {"status": "ok", "name": search_city, "note": note}

    for cat in ["restaurants", "hotels"]:
        if needed(cat):
            res[cat] = get_places.invoke(
                {"city": search_city, "category": cat, "limit": 8})

    if needed("weather"):
        res["weather"] = get_weather.invoke(
            {"city": search_city, "start_date": start, "end_date": end})

    if needed("info"):
        res["info"] = search_web.invoke(
            {"query": f"{city} travel guide typical hotel and food prices PKR"})

    if needed("routes"):
        attractions = res["attractions"]
        if attractions.get("status") == "ok":
            center = attractions["center"]
            legs = []
            for p in attractions["places"][:3]:
                r = get_route.invoke({
                    "start_lat": center["lat"], "start_lon": center["lon"],
                    "end_lat": p["lat"], "end_lon": p["lon"]})
                if r.get("status") == "ok":
                    legs.append({"to": p["name"], **r})
            res["routes"] = {"status": "ok" if legs else "empty", "legs": legs}
        else:
            res["routes"] = {"status": "error",
                             "message": "No attractions, so routes skipped"}

    return {"research": res}


# ---------- Node 3: plan ----------
def plan_node(state: AgentState):
    """Ask the LLM for an itinerary, with a reason for every day."""
    trip = state["trip"]
    planner = llm.with_structured_output(TripPlan)
    prompt = f"""You are a travel planner. Create a {trip['days']}-day plan
for {trip['destination']} for {trip['travelers']} traveler(s).
Total budget: PKR {trip['budget_pkr']}.

Research data (some parts may be missing or failed):
{compact_research(state['research'])}

Rules:
- Only recommend places and hotels that appear in the research data.
- Every day must have a 'reason' explaining why these places were chosen
  (budget, distance from center, weather).
- If research data is missing, say so in cost_reasoning. Do not invent facts.
- All prices are your estimates in PKR. Use prices from the search info if present.
- The final total will include a 10 percent contingency, so plan to stay
  under budget after adding it.
- In cost_reasoning, explain how each price was chosen, but do NOT state any totals or sums.
- Only quote distances that appear in the routes data. Do not mention weather details other than temperature and rain chance.

Feedback from previous attempt: {state.get('feedback', 'none')}"""
    plan = call_llm(planner, prompt)
    return {"plan": plan.model_dump()}


# ---------- Node 4: cost ----------
def cost_node(state: AgentState):
    """Calculate the total cost with Python, not the LLM."""
    t, p = state["trip"], state["plan"]
    cost = estimate_cost.invoke({
        "days": t["days"],
        "travelers": t["travelers"],
        "budget": t["budget_pkr"],
        "hotel_per_night": p["hotel_per_night"],
        "transport_total": p["transport_total"],
        "food_per_person_per_day": p["food_per_person_per_day"],
        "activities_total": p["activities_total"],
    })
    return {"cost": cost}


# ---------- Node 5: critic ----------
def critic_node(state: AgentState):
    """Check failed tools and budget, then decide retry, replan or finalize."""
    research, cost = state["research"], state["cost"]
    failed = [k for k, v in research.items() if v.get("status") != "ok"]

    if failed and state["research_retries"] < MAX_RESEARCH_RETRIES:
        return {
            "decision": "retry_research",
            "research_retries": state["research_retries"] + 1,
        }

    if cost.get("status") == "ok" and not cost["within_budget"] \
            and state["replans"] < MAX_REPLANS:
        return {
            "decision": "replan",
            "replans": state["replans"] + 1,
            "feedback": (
                f"Your plan cost PKR {cost['total']} but the budget is "
                f"PKR {cost['budget']}. Cut at least PKR {cost['shortfall']} "
                "(cheaper hotel, transport or food)."
            ),
        }

    warnings = []
    for k in failed:
        msg = research[k].get("message", "returned no data")
        warnings.append(
            f"'{k}' data unavailable ({msg}). "
            "Plan for this part is based on estimates only."
        )
    if cost.get("status") != "ok":
        warnings.append("Cost could not be calculated.")
    elif not cost["within_budget"]:
        warnings.append(
            f"OVER BUDGET: estimated PKR {cost['total']} vs budget "
            f"PKR {cost['budget']} (short by PKR {cost['shortfall']}). "
            "Consider a higher budget or fewer days."
        )
    return {"decision": "finalize", "warnings": warnings}


# ---------- Node 6: finalize ----------
def finalize_node(state: AgentState):
    """Build the final answer in Python so warnings are never dropped."""
    t, p, c = state["trip"], state["plan"], state["cost"]
    note = state["research"].get("city_used", {}).get("note", "")

    lines = [
        f"TRIP PLAN: {t['destination']} | {t['days']} days | "
        f"Budget PKR {t['budget_pkr']}",
        "",
    ]
    if note:
        lines += [f"Note: {note}", ""]
    lines += [f"Hotel: {p['hotel_name']} (PKR {p['hotel_per_night']}/night)", ""]

    for d in p["days"]:
        lines.append(f"Day {d['day']}: " + ", ".join(d["activities"]))
        lines.append(f"   Why: {d['reason']}")

    lines += ["", "COST BREAKDOWN (PKR):"]
    if c.get("status") == "ok":
        for k, v in c["breakdown"].items():
            lines.append(f"   {k}: {v}")
        lines.append(f"   TOTAL: {c['total']} (budget {c['budget']})")
    else:
        lines.append("   Not available")

    lines += ["", f"Cost reasoning: {p['cost_reasoning']}"]

    if state["warnings"]:
        lines += ["", "WARNINGS:"] + [f" - {w}" for w in state["warnings"]]

    return {"final": "\n".join(lines)}


# ---------- Graph jodna ----------
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("parse", parse_node)
    g.add_node("research", research_node)
    g.add_node("plan", plan_node)
    g.add_node("cost", cost_node)
    g.add_node("critic", critic_node)
    g.add_node("finalize", finalize_node)

    g.add_edge(START, "parse")
    g.add_edge("parse", "research")
    g.add_edge("research", "plan")
    g.add_edge("plan", "cost")
    g.add_edge("cost", "critic")
    g.add_conditional_edges(
        "critic",
        lambda s: s["decision"],
        {
            "retry_research": "research",
            "replan": "plan",
            "finalize": "finalize",
        },
    )
    g.add_edge("finalize", END)
    return g.compile()