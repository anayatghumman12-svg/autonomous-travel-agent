from tools.places import get_places

for cat in ["attractions", "restaurants", "hotels"]:
    result = get_places.invoke({"city": "Karimabad", "category": cat, "limit": 5})
    print(cat, "->", result["status"])
    for p in result.get("places", []):
        print("   ", p["name"], p["lat"], p["lon"])