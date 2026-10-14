# Autonomous Travel Planning Agent

An agent built with **LangChain** and **LangGraph** that plans a multi-day trip from a single sentence such as:

> "Plan a 5-day trip to Hunza under PKR 120,000."

It researches the destination with separate tools, estimates the cost in Python, explains every recommendation, and a Critic node makes sure a plan is never silently over budget or built on failed tool calls.

---

## 1. Architecture

START -> parse -> research -> plan -> cost -> critic --+--> finalize -> END
^          ^                       |
|          +---- replan -----------+
+---------- retry_research -------+


| Node | What it does |
|---|---|
| **parse** | The LLM extracts destination, days, budget, travelers and start date into a Pydantic schema (structured output). |
| **research** | Calls the Places, Weather, Search and Routing tools directly from code. On a retry, only the tools that failed or returned nothing are called again. |
| **plan** | The LLM writes a day-by-day itinerary and estimates unit prices. Every day must include a `reason`. It may only use places that appear in the research data. |
| **cost** | The Cost Estimator tool calculates the total in Python (not by the LLM) and compares it with the budget. |
| **critic** | Rule-based checks (see section 5). Decides: `retry_research`, `replan` or `finalize`. |
| **finalize** | Builds the final answer from a Python template so warnings can never be dropped. |

**State** is a shared dictionary (`AgentState`) that every node reads and updates (`trip`, `research`, `plan`, `cost`, `feedback`, counters, `warnings`, `final`).

Loop limits (`MAX_REPLANS = 2`, `MAX_RESEARCH_RETRIES = 1`) prevent infinite loops.

---

## 2. Tools

Each tool is a separate `@tool` function in `tools/`. All tools return a dictionary with `status` set to `ok`, `empty` or `error`, so the Critic can react to each case.

| Tool | File | API | Returns |
|---|---|---|---|
| Weather | `tools/weather.py` | Open-Meteo | Daily min/max temperature and rain probability for the trip dates |
| Places | `tools/places.py` | Geoapify | Attractions, restaurants, hotels, museums, landmarks (name, category, coordinates, address) |
| Routing | `tools/routing.py` | OpenRouteService | Driving and walking distance (km) and time (min) between two points |
| Search | `tools/search.py` | Tavily | Short answer and top sources about the destination and typical prices |
| Cost Estimator | `tools/cost.py` | none | Hotel + transport + food + activities + 10% contingency vs budget |

### Cost formula

nights      = max(days - 1, 1)
rooms       = ceil(travelers / 2)
hotel       = hotel_per_night * nights * rooms
food        = food_per_person_per_day * days * travelers
subtotal    = hotel + transport_total + food + activities_total
contingency = round(subtotal * 0.10)
total       = subtotal + contingency


---

## 3. Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
Create a .env file in the project root (never commit it):

GEOAPIFY_API_KEY=...
ORS_API_KEY=...
TAVILY_API_KEY=...
GOOGLE_API_KEY=...
LLM_MODEL=...