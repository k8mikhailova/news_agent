"""
The agent's one tool: search for news articles on any query.

Real mode uses NewsAPI.org (free tier: https://newsapi.org/register).
Mock mode returns canned fixture data so you can test the AGENT LOGIC
without burning API calls or needing a key yet.
"""

import os
import requests

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# Toggle this off once you have a real NEWS_API_KEY and want live results.
MOCK_MODE = NEWS_API_KEY is None


# Small fixture dataset so the agent loop is testable offline.
_MOCK_ARTICLES = {
    "politics": [
        {"title": "Senate advances bipartisan infrastructure funding bill",
         "description": "A funding package cleared a key procedural vote after weeks of negotiation.",
         "source": "Reuters", "url": "https://example.com/a1"},
        {"title": "State governors meet on shared water rights dispute",
         "description": "Western states discuss a long-running disagreement over river allocation.",
         "source": "AP", "url": "https://example.com/a2"},
    ],
    "tech": [
        {"title": "Chipmaker unveils next-gen AI accelerator",
         "description": "The new chip claims a significant efficiency gain over last year's model.",
         "source": "The Verge", "url": "https://example.com/a3"},
        {"title": "Open-source database project hits major milestone",
         "description": "The project passed 50k GitHub stars amid rising enterprise adoption.",
         "source": "TechCrunch", "url": "https://example.com/a4"},
    ],
    "default": [
        {"title": "Regional heatwave breaks decade-old temperature record",
         "description": "Meteorologists point to a persistent high-pressure system.",
         "source": "AP", "url": "https://example.com/a5"},
    ],
}


def search_news(query: str, max_results: int = 5) -> list[dict]:
    """
    Search for recent news articles matching `query`.

    Returns a list of dicts: {title, description, source, url}
    """
    if MOCK_MODE:
        query_lower = query.lower()
        if "politic" in query_lower:
            results = _MOCK_ARTICLES["politics"]
        elif "tech" in query_lower:
            results = _MOCK_ARTICLES["tech"]
        else:
            results = _MOCK_ARTICLES["default"]
        return results[:max_results]

    # Real NewsAPI call
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": max_results,
            "apiKey": NEWS_API_KEY,
        },
        timeout=10,
    )
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    return [
        {
            "title": a["title"],
            "description": a.get("description") or "",
            "source": a["source"]["name"],
            "url": a["url"],
        }
        for a in articles
    ]
