import os
import requests
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("GEOAPIFY_API_KEY")

for city in ["Hunza", "Karimabad", "Gilgit", "Lahore"]:
    g = requests.get("https://api.geoapify.com/v1/geocode/search",
                     params={"text": city, "limit": 1, "apiKey": KEY}, timeout=10)
    feats = g.json().get("features", [])
    if not feats:
        print(city, "-> geocode: nothing found")
        continue
    p = feats[0]["properties"]
    lon, lat = p["lon"], p["lat"]
    print(f"\n{city} -> {p.get('formatted')} ({lat}, {lon})")

    r = requests.get("https://api.geoapify.com/v2/places",
                     params={"categories": "catering.restaurant",
                             "filter": f"circle:{lon},{lat},15000",
                             "limit": 5, "apiKey": KEY}, timeout=10)
    print("   places status:", r.status_code,
          "| results:", len(r.json().get("features", [])))