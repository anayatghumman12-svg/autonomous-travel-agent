import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Geoapify
r = requests.get("https://api.geoapify.com/v1/geocode/search",
                 params={"text": "Hunza", "apiKey": os.getenv("GEOAPIFY_API_KEY")})
print("Geoapify:", r.status_code)

# OpenRouteService
r = requests.post("https://api.openrouteservice.org/v2/directions/driving-car",
                  json={"coordinates": [[74.65, 36.32], [74.66, 36.31]]},
                  headers={"Authorization": os.getenv("ORS_API_KEY")})
print("ORS:", r.status_code)

# Tavily
r = requests.post("https://api.tavily.com/search",
                  headers={"Authorization": f"Bearer {os.getenv('TAVILY_API_KEY')}"},
                  json={"query": "Hunza travel", "max_results": 1})
print("Tavily:", r.status_code)

# Open-Meteo (key nahi chahiye)
r = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                 params={"name": "Hunza", "count": 1})
print("Open-Meteo:", r.status_code)