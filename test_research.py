from graph import research_node

state = {
    "trip": {"destination": "Hunza", "days": 5, "budget_pkr": 120000,
             "travelers": 1, "start_date": ""},
    "research": {},
}

out = research_node(state)["research"]

for key, value in out.items():
    print(key, "->", value.get("status"))

print("City used:", out["city_used"])
print("Routes:", out["routes"])
print("Weather:", out["weather"])