"""Web Search — DuckDuckGo search, no API key needed.

Usage:
    from web_search import web_search
    results = web_search("python tutorials")
"""

import sys


def web_search(query: str, max_results: int = 3) -> str:
    """Search DuckDuckGo and return top results as text."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return ""
        formatted = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            snippet = r.get("body", "")
            formatted.append(f"{i}. {title}: {snippet}")
        return "\n".join(formatted)
    except ImportError:
        return ""
    except Exception:
        return ""
