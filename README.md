**Autonomous Travel Planning Agent**

An autonomous agent built with **LangChain** and **LangGraph** that plans a multi-day trip end-to-end from a single sentence prompt such as:

> "Plan a 5-day trip to Hunza under PKR 120,000."

The agent researches destinations using separate discrete tools, calculates exact costs in Python, explains every recommendation with solid reasoning, and features a rule-based **Critic/Reflection node** to catch budget overruns and tool failures.

---

## 1. Architecture

START -> parse -> research -> plan -> cost -> critic --+--> finalize -> END
^          ^                       |
|          +---- replan -----------+
+---------- retry_research -------+


| Node | What it does |
|---|---|
| **parse** | Extracts destination, duration, budget, travelers, and start date into a Pydantic structured output schema. |
| **research** | Invokes Places, Weather, Search, and Routing tools. On retry, only the tools that previously failed or returned empty data are executed again. |
| **plan** | Generates a day-by-day itinerary with explicit reasons for every recommendation, restricted strictly to researched data. |
| **cost** | Calculates exact trip expenses using pure Python calculation logic. |
| **critic** | Rule-based evaluation node that checks budget constraints and tool statuses, deciding whether to `retry_research`, `replan`, or `finalize`. |
| **finalize** | Formats the final trip report from a Python template to ensure no warnings or shortfalls are ever omitted. |

* **State Management:** Uses a shared dictionary (`AgentState`) tracked across all nodes.
* **Guardrails:** Loop limiters (`MAX_REPLANS = 2`, `MAX_RESEARCH_RETRIES = 1`) prevent infinite loops.

---

## 2. Tools & Cost Formula

Each tool is implemented as an independent `@tool` function returning consistent statuses (`ok`, `empty`, or `error`) for the Critic node.

| Tool | File | API Source | Key Returns |
|---|---|---|---|
| Weather | `tools/weather.py` | Open-Meteo | Daily min/max temperature & rain probability |
| Places | `tools/places.py` | Geoapify | Attractions, restaurants, hotels (name, category, coordinates) |
| Routing | `tools/routing.py` | OpenRouteService | Driving & walking distance (km) and duration (min) |
| Search | `tools/search.py` | Tavily | Short answer & top destination sources/pricing |
| Cost Estimator | `tools/cost.py` | Python Logic | Hotel + transport + food + activities + 10% contingency vs. budget |

### Cost Calculation Formula
```python
nights      = max(days - 1, 1)
rooms       = ceil(travelers / 2)
hotel       = hotel_per_night * nights * rooms
food        = food_per_person_per_day * days * travelers
subtotal    = hotel + transport_total + food + activities_total
contingency = round(subtotal * 0.10)
total       = subtotal + contingency
3. Setup & Installation
Bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
Create a .env file in the project root directory (never commit this file to version control):

Code snippet
GEOAPIFY_API_KEY=your_geoapify_key_here
ORS_API_KEY=your_openrouteservice_key_here
TAVILY_API_KEY=your_tavily_key_here
GOOGLE_API_KEY=your_google_ai_studio_key_here
LLM_MODEL=gemini-2.5-flash
Running the Agent
Run the main execution script with a default or custom prompt:

Bash
python main.py
python main.py "Plan a 3-day trip to Lahore for 2 people, budget 50000 rupees"
4. API Research & Selection
4.1 Place Search
Geoapify Places (Selected): Offers a generous free tier (3,000 req/day), category/radius filters, and geographic coordinates in a single call without requiring a credit card.

Alternatives Evaluated: Google Places (requires billing card), OpenStreetMap/Nominatim (strict rate limits).

4.2 Weather Forecast
Open-Meteo (Selected): Requires no API key registration, offers 10,000 requests/day, and provides precise temperature ranges and precipitation probabilities.

Alternatives Evaluated: OpenWeatherMap, WeatherAPI.

4.3 Routing & Distance
OpenRouteService (Selected): Free tier with robust routing profiles (driving/walking) returning precise distances and durations. (Note: Migrating infrastructure to api.heigit.org).

Alternatives Evaluated: Mapbox Directions, Google Directions.

4.4 Web Search
Tavily AI (Selected): Specifically engineered for LLM agents, returning clean text snippets and short answers to keep prompt tokens lightweight.

Alternatives Evaluated: Serper.dev, DuckDuckGo.

4.5 LLM
Google Gemini via AI Studio (gemini-2.5-flash / gemini-3.7-flash): Provides structured output support via LangChain Pydantic schemas with robust speed and reliability.

5. Reflection / Critic Node
The Critic node operates via deterministic Python rules rather than LLM inference to ensure strict budget enforcement:

Tool Failure Handling: If a tool returns no data or fails, the graph triggers a targeted retry_research loop.

Budget Enforcement: If estimated totals exceed the budget, the graph triggers a replan loop with feedback instructing the planner to cut costs.

Transparency: Unresolved tool failures or budget shortfalls are never hidden; they are explicitly flagged as WARNINGS in the final output.

Geographical Alias Fallback: Automatically maps broad regional inputs like "Hunza" to their central hubs (e.g., "Karimabad") to prevent empty geocoding results.

6. Project Structure
travel_agent/
├── main.py
├── graph.py
├── requirements.txt
├── .env            (excluded via .gitignore)
├── .gitignore
└── tools/
    ├── __init__.py
    ├── weather.py
    ├── places.py
    ├── routing.py
    ├── search.py
    └── cost.py
