from tools.search import search_web

result = search_web.invoke({"query": "Hunza Karimabad travel guide hotel prices PKR"})
print("status:", result["status"])
print("answer:", result.get("answer", ""))
for s in result.get("sources", []):
    print("-", s["title"], s["url"])