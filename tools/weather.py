import requests
from langchain_core.tools import tool

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@tool
def get_weather(city: str, start_date: str, end_date: str) -> dict:
    """Get daily weather forecast for a city between two dates (YYYY-MM-DD).
    Returns temperature range and rain probability for each day."""
    try:
        geo = requests.get(
            GEOCODE_URL, params={"name": city, "count": 1}, timeout=10
        )
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            return {"status": "error", "message": f"City '{city}' not found"}

        lat = results[0]["latitude"]
        lon = results[0]["longitude"]

        forecast = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "start_date": start_date,
                "end_date": end_date,
                "timezone": "auto",
            },
            timeout=10,
        )
        forecast.raise_for_status()
        daily = forecast.json()["daily"]

        days = []
        for i in range(len(daily["time"])):
            days.append({
                "date": daily["time"][i],
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "rain_chance_percent": daily["precipitation_probability_max"][i],
            })
        return {"status": "ok", "city": city, "lat": lat, "lon": lon, "days": days}

    except requests.RequestException as e:
        return {"status": "error", "message": f"Weather API failed: {e}"}