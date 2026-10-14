import math
from langchain_core.tools import tool

CONTINGENCY_RATE = 0.10
PEOPLE_PER_ROOM = 2


@tool
def estimate_cost(
    days: int,
    travelers: int,
    budget: int,
    hotel_per_night: int,
    transport_total: int,
    food_per_person_per_day: int,
    activities_total: int,
) -> dict:
    """Calculate total trip cost in PKR from hotel, transport, food and
    activities, and compare it against the budget. Includes a 10 percent
    contingency buffer."""
    values = [days, travelers, budget, hotel_per_night,
              transport_total, food_per_person_per_day, activities_total]
    if days < 1 or travelers < 1 or any(v < 0 for v in values):
        return {"status": "error", "message": "Invalid numbers given"}

    nights = max(days - 1, 1)
    rooms = math.ceil(travelers / PEOPLE_PER_ROOM)

    hotel = hotel_per_night * nights * rooms
    food = food_per_person_per_day * days * travelers
    subtotal = hotel + transport_total + food + activities_total
    contingency = round(subtotal * CONTINGENCY_RATE)
    total = subtotal + contingency

    within_budget = total <= budget
    return {
        "status": "ok",
        "breakdown": {
            "hotel": hotel,
            "transport": transport_total,
            "food": food,
            "activities": activities_total,
            "contingency": contingency,
        },
        "total": total,
        "budget": budget,
        "within_budget": within_budget,
        "remaining": budget - total if within_budget else 0,
        "shortfall": 0 if within_budget else total - budget,
    }