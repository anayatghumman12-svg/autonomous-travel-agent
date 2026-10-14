from tools.routing import get_route

result = get_route.invoke({
    "start_lat": 36.325583, "start_lon": 74.6687787,
    "end_lat": 36.323873, "end_lon": 74.6905018,
})
print(result)