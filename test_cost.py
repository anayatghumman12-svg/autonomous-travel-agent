from tools.cost import estimate_cost

# Test 1: thoda over budget
print(estimate_cost.invoke({
    "days": 5, "travelers": 2, "budget": 120000,
    "hotel_per_night": 8000, "transport_total": 40000,
    "food_per_person_per_day": 3000, "activities_total": 10000,
}))

# Test 2: budget ke andar
print(estimate_cost.invoke({
    "days": 5, "travelers": 2, "budget": 150000,
    "hotel_per_night": 8000, "transport_total": 40000,
    "food_per_person_per_day": 3000, "activities_total": 10000,
}))

# Test 3: ghalat input
print(estimate_cost.invoke({
    "days": 0, "travelers": 2, "budget": 150000,
    "hotel_per_night": 8000, "transport_total": 40000,
    "food_per_person_per_day": 3000, "activities_total": 10000,
}))