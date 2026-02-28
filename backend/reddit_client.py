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

# Rate-limit: Reddit allows ~10 req/min for unauthenticated
RATE_LIMIT_DELAY = 1.5  # seconds between requests


async def search_reddit(
    query: str,
    subreddits: Optional[list[str]] = None,
    limit: int = 10,
    sort: str = "relevance",
    time_filter: str = "all",
) -> list[dict]:
    """
    Search Reddit for threads matching the query.
    If subreddits are provided, searches each one individually and merges results.
    Otherwise does a global search.

    Returns a list of simplified thread dicts.
    """
    all_threads = []

    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        if subreddits:
            # Search specific subreddits + global
            search_targets = [
                (REDDIT_SUBREDDIT_SEARCH_URL.format(
                    subreddit=sub.replace("r/", "")), sub)
                for sub in subreddits[:3]  # cap at 3 subreddits per query
            ]
            # Also add global search
            search_targets.append((REDDIT_SEARCH_URL, "all"))
        else:
            search_targets = [(REDDIT_SEARCH_URL, "all")]

        for url, source in search_targets:
            try:
                params = {
                    "q": query,
                    "limit": min(limit, 25),
                    "sort": sort,
                    "t": time_filter,
                    "restrict_sr": "on" if source != "all" else "off",
                    "type": "link",
                }
                response = await client.get(url, params=params)

                if response.status_code == 429:
                    logger.warning("Reddit rate limit hit, waiting 5s...")
                    await asyncio.sleep(5)
                    response = await client.get(url, params=params)

                if response.status_code != 200:
                    logger.warning(
                        f"Reddit returned {response.status_code} for {url}")
                    continue

                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    p = post.get("data", {})
                    thread = {
                        "id": p.get("id", ""),
                        "title": p.get("title", ""),
                        # truncate long posts
                        "selftext": (p.get("selftext", "") or "")[:1500],
                        "subreddit": p.get("subreddit_name_prefixed", ""),
                        "score": p.get("score", 0),
                        "num_comments": p.get("num_comments", 0),
                        "url": f"https://reddit.com{p.get('permalink', '')}",
                        "created_utc": p.get("created_utc", 0),
                        "upvote_ratio": p.get("upvote_ratio", 0),
                        "source_query": query,
                    }
                    # Dedupe by id
                    if thread["id"] and thread["id"] not in {t["id"] for t in all_threads}:
                        all_threads.append(thread)

                await asyncio.sleep(RATE_LIMIT_DELAY)

            except httpx.TimeoutException:
                logger.warning(f"Timeout searching Reddit: {url}")
            except Exception as e:
                logger.warning(f"Error searching Reddit: {e}")

    return all_threads


async def fetch_thread_comments(thread_url: str, limit: int = 10) -> list[str]:
    """
    Fetch top comments from a specific Reddit thread.
    Returns a list of comment body strings.
    """
    json_url = thread_url.rstrip("/") + ".json"

    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        try:
            response = await client.get(json_url, params={"limit": limit, "sort": "top"})
            if response.status_code != 200:
                return []

            data = response.json()
            if len(data) < 2:
                return []

            comments = []
            comment_listing = data[1].get("data", {}).get("children", [])
            for c in comment_listing:
                body = c.get("data", {}).get("body", "")
                if body and body != "[deleted]" and body != "[removed]":
                    comments.append(body[:500])  # truncate long comments
                    if len(comments) >= limit:
                        break

            return comments

        except Exception as e:
            logger.warning(f"Error fetching comments: {e}")
            return []
