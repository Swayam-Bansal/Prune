"""
Reddit search client — uses Reddit's public JSON API (no auth required).
Searches posts and returns structured thread data.
"""

import httpx
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

REDDIT_SEARCH_URL = "https://www.reddit.com/search.json"
REDDIT_SUBREDDIT_SEARCH_URL = "https://www.reddit.com/r/{subreddit}/search.json"

HEADERS = {
    "User-Agent": "PreMortem:v1.0 (market research tool)",
}

# Global semaphore: max concurrent Reddit HTTP requests
# Keeps us well under Reddit's ~60 req/min unauthenticated ceiling
_REDDIT_SEM: asyncio.Semaphore | None = None


def _sem() -> asyncio.Semaphore:
    global _REDDIT_SEM
    if _REDDIT_SEM is None:
        _REDDIT_SEM = asyncio.Semaphore(5)
    return _REDDIT_SEM


async def _fetch_one(
    client: httpx.AsyncClient,
    url: str,
    params: dict,
    query: str,
) -> list[dict]:
    """Single Reddit search request, semaphore-gated."""
    async with _sem():
        try:
            response = await client.get(url, params=params)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 3))
                logger.warning(f"Reddit rate limit hit, waiting {retry_after}s...")
                await asyncio.sleep(retry_after)
                response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.warning(f"Reddit returned {response.status_code} for {url}")
                return []
            posts = response.json().get("data", {}).get("children", [])
            return [
                {
                    "id": p["data"].get("id", ""),
                    "title": p["data"].get("title", ""),
                    "selftext": (p["data"].get("selftext", "") or "")[:1500],
                    "subreddit": p["data"].get("subreddit_name_prefixed", ""),
                    "score": p["data"].get("score", 0),
                    "num_comments": p["data"].get("num_comments", 0),
                    "url": f"https://reddit.com{p['data'].get('permalink', '')}",
                    "created_utc": p["data"].get("created_utc", 0),
                    "upvote_ratio": p["data"].get("upvote_ratio", 0),
                    "source_query": query,
                }
                for p in posts
                if p.get("data", {}).get("id")
            ]
        except httpx.TimeoutException:
            logger.warning(f"Timeout searching Reddit: {url}")
            return []
        except Exception as e:
            logger.warning(f"Error searching Reddit: {e}")
            return []


async def search_reddit(
    query: str,
    subreddits: Optional[list[str]] = None,
    limit: int = 10,
    sort: str = "relevance",
    time_filter: str = "all",
) -> list[dict]:
    """
    Search Reddit for threads matching the query.
    All search targets (subreddits + global) are fetched concurrently.
    Returns a deduplicated list of thread dicts.
    """
    if subreddits:
        search_targets = [
            (REDDIT_SUBREDDIT_SEARCH_URL.format(subreddit=sub.replace("r/", "")), sub)
            for sub in subreddits[:3]
        ]
        search_targets.append((REDDIT_SEARCH_URL, "all"))
    else:
        search_targets = [(REDDIT_SEARCH_URL, "all")]

    base_params = {"limit": min(limit, 25), "sort": sort, "t": time_filter, "type": "link"}

    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        results = await asyncio.gather(*[
            _fetch_one(
                client,
                url,
                {**base_params, "q": query, "restrict_sr": "on" if source != "all" else "off"},
                query,
            )
            for url, source in search_targets
        ])

    seen: set[str] = set()
    all_threads: list[dict] = []
    for batch in results:
        for t in batch:
            if t["id"] not in seen:
                seen.add(t["id"])
                all_threads.append(t)
    return all_threads


async def fetch_thread_comments(thread_url: str, limit: int = 10) -> list[str]:
    """
    Fetch top comments from a specific Reddit thread.
    Returns a list of comment body strings.
    """
    json_url = thread_url.rstrip("/") + ".json"
    async with _sem():
        async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
            try:
                response = await client.get(json_url, params={"limit": limit, "sort": "top"})
                if response.status_code != 200:
                    return []
                data = response.json()
                if len(data) < 2:
                    return []
                comments = []
                for c in data[1].get("data", {}).get("children", []):
                    body = c.get("data", {}).get("body", "")
                    if body and body not in ("[deleted]", "[removed]"):
                        comments.append(body[:500])
                        if len(comments) >= limit:
                            break
                return comments
            except Exception as e:
                logger.warning(f"Error fetching comments: {e}")
                return []
