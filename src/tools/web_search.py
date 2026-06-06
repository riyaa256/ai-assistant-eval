def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    f"**{r['title']}**\n{r['body']}\nSource: {r['href']}"
                )
        if not results:
            return f"No results found for: {query}"
        return "\n\n---\n\n".join(results)
    except ImportError:
        return "Web search unavailable (duckduckgo_search not installed)"
    except Exception as e:
        return f"Search error: {str(e)}"
