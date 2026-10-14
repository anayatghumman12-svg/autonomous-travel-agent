from graph import research_node, plan_node, cost_node

state = {
    "trip": {"destination": "Hunza", "days": 5, "budget_pkr": 120000,
             "travelers": 1, "start_date": ""},
    "research": {},
}

state["research"] = research_node(state)["research"]
state["plan"] = plan_node(state)["plan"]
state["cost"] = cost_node(state)["cost"]

p = state["plan"]
print("Hotel:", p["hotel_name"], "| per night:", p["hotel_per_night"])
for d in p["days"]:
    print(f"Day {d['day']}:", d["activities"])
    print("   Why:", d["reason"])
print("Cost reasoning:", p["cost_reasoning"])
print("COST:", state["cost"])
print("Hotels in research:",
      [h["name"] for h in state["research"]["hotels"].get("places", [])])