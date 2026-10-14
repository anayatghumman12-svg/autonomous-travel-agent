import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_URL = "https://api.tavily.com/search"


@tool
def search_web(query: str) -> dict:
    """Search the web for tourist information, travel tips and typical
    prices about a destination. Returns a short answer and top sources."""
    if not API_KEY:
        return {"status": "error", "message": "TAVILY_API_KEY missing in .env"}

    try:
        resp = requests.post(
            TAVILY_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"query": query, "max_results": 5, "include_answer": True},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()

        sources = []
        for r in data.get("results", []):
            sources.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:300],
            })

        if not sources and not data.get("answer"):
            return {"status": "empty", "message": f"No results for '{query}'"}

        return {"status": "ok", "answer": data.get("answer", ""), "sources": sources}

    except requests.RequestException as e:
        return {"status": "error", "message": f"Search API failed: {e}"}