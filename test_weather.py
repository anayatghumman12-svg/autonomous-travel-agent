from tools.weather import get_weather

result = get_weather.invoke({
    "city": "Karimabad",
    "start_date": "2026-10-20",
    "end_date": "2026-10-24",
})
print(result)