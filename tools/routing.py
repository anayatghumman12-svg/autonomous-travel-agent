import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

API_KEY = os.getenv("ORS_API_KEY")
ORS_URL = "https://api.openrouteservice.org/v2/directions/{profile}"


def _call_ors(profile, coords):
    resp = requests.post(
        ORS_URL.format(profile=profile),
        json={"coordinates": coords},
        headers={"Authorization": API_KEY, "Content-Type": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    summary = resp.json()["routes"][0]["summary"]
    return round(summary["distance"] / 1000, 1), round(summary["duration"] / 60)


@tool
def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict:
    """Get driving distance (km) and time (minutes), plus walking distance
    and time, between two coordinates."""
    if not API_KEY:
        return {"status": "error", "message": "ORS_API_KEY missing in .env"}

    coords = [[start_lon, start_lat], [end_lon, end_lat]]

    try:
        drive_km, drive_min = _call_ors("driving-car", coords)
    except (requests.RequestException, KeyError, IndexError) as e:
        return {"status": "error", "message": f"Driving route failed: {e}"}

    try:
        walk_km, walk_min = _call_ors("foot-walking", coords)
    except (requests.RequestException, KeyError, IndexError):
        walk_km, walk_min = None, None

    return {
        "status": "ok",
        "driving_km": drive_km,
        "driving_minutes": drive_min,
        "walking_km": walk_km,
        "walking_minutes": walk_min,
    }