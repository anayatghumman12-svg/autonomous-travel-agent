import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

API_KEY = os.getenv("GEOAPIFY_API_KEY")
GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
PLACES_URL = "https://api.geoapify.com/v2/places"

CATEGORY_MAP = {
    "attractions": "tourism.attraction",
    "restaurants": "catering.restaurant",
    "museums": "entertainment.museum",
    "hotels": "accommodation.hotel",
    "landmarks": "heritage",
}


@tool
def get_places(city: str, category: str, limit: int = 10) -> dict:
    """Find places near a city. category must be one of: attractions,
    restaurants, museums, hotels, landmarks. Returns name, category,
    latitude and longitude of each place."""
    if category not in CATEGORY_MAP:
        return {
            "status": "error",
            "message": f"Unknown category '{category}'. Use: {list(CATEGORY_MAP)}",
        }
    if not API_KEY:
        return {"status": "error", "message": "GEOAPIFY_API_KEY missing in .env"}

    try:
        geo = requests.get(
            GEOCODE_URL,
            params={"text": city, "limit": 1, "apiKey": API_KEY},
            timeout=10,
        )
        geo.raise_for_status()
        features = geo.json().get("features")
        if not features:
            return {"status": "error", "message": f"City '{city}' not found"}

        lon = features[0]["properties"]["lon"]
        lat = features[0]["properties"]["lat"]

        resp = requests.get(
            PLACES_URL,
            params={
                "categories": CATEGORY_MAP[category],
                "filter": f"circle:{lon},{lat},15000",
                "bias": f"proximity:{lon},{lat}",
                "limit": limit,
                "apiKey": API_KEY,
            },
            timeout=10,
        )
        resp.raise_for_status()

        places = []
        for f in resp.json().get("features", []):
            p = f["properties"]
            if not p.get("name"):
                continue
            places.append({
                "name": p["name"],
                "category": category,
                "lat": p["lat"],
                "lon": p["lon"],
                "address": p.get("formatted", ""),
            })

        if not places:
            return {
                "status": "empty",
                "message": f"No {category} found near {city}",
                "places": [],
            }
        return {"status": "ok", "city": city, "center": {"lat": lat, "lon": lon}, "places": places}

    except requests.RequestException as e:
        return {"status": "error", "message": f"Places API failed: {e}"}