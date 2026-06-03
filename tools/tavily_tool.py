import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

def tavily_search(query: str) -> str:
    api_key = (os.getenv("TAVILY_API_KEY") or "").strip(" ;\"'")
    if not api_key:
        return "TAVILY_API_KEY is missing. Add it to your .env file."

    try:
        client = TavilyClient(api_key=api_key)

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
        )

        results = response.get("results", [])

        if not results:
            return f"No Tavily search results found for: {query}"

        formatted_results = []

        for item in results:
            title = item.get("title", "No title")
            url = item.get("url", "No URL")
            content = item.get("content", "No content")

            formatted_results.append(
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Content: {content}\n"
            )

        return "\n---\n".join(formatted_results)

    except Exception as error:
        return f"Tavily search failed: {error}"