"""
GitHub Competition Signal Engine
=================================
Extracted from the original main.py on the `main` branch.
Handles keyword extraction, GitHub repo search, competition risk scoring,
and relevance ranking.
"""

import json
import logging
import os
import re
from typing import List

import requests
from fastapi import HTTPException

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/search/repositories"


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

def extract_keywords(text: str) -> List[str]:
    """Extract core keywords from an idea string.

    Uses Gemini when GEMINI_API_KEY is set; otherwise falls back to the first
    five non-trivial words of the input (deterministic, no network required).
    """
    if os.getenv("GEMINI_API_KEY"):
        try:
            import google.generativeai as genai

            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "Extract 3-5 domain-specific technical keywords from this startup idea that would help find similar GitHub projects. "
                "Focus on: technology names, problem domains, specific tools/platforms mentioned (e.g., 'jira', 'slack', 'transcript'). "
                "Avoid generic words like 'ai', 'app', 'tool', 'automatically'. "
                "Return ONLY a valid JSON array of lowercase strings with NO additional text or markdown formatting.\n\n"
                f"Startup idea: {text}\n\n"
                "JSON array:"
            )
            response = model.generate_content(prompt)
            raw = (getattr(response, "text", "") or "").strip()
            logger.info(f"Gemini raw response: {raw}")

            # Try to extract JSON from markdown code blocks if present
            if "```" in raw:
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
                if json_match:
                    raw = json_match.group(1).strip()

            keywords = json.loads(raw)
            if isinstance(keywords, list):
                return [str(k).lower() for k in keywords[:5]]
        except Exception as e:
            logger.warning(f"Gemini keyword extraction failed: {e}")

    # Fallback: first 5 words stripped of punctuation
    stop_words = {"a", "an", "the", "is", "for", "and", "or", "to", "of", "in", "that", "with"}
    words = [
        w.strip(".,!?;:\"'()[]{}").lower()
        for w in text.split()
        if w.strip(".,!?;:\"'()[]{}").lower() not in stop_words
    ]
    return words[:5]


# ---------------------------------------------------------------------------
# GitHub query building
# ---------------------------------------------------------------------------

def build_github_query(keywords: List[str]) -> str:
    """Build a GitHub search query from extracted keywords."""
    weak = {
        "ai", "automatically", "turn", "turns", "build", "building",
        "make", "makes", "small", "large", "simple", "easy", "quick",
        "app", "tool", "platform", "system", "using", "based", "create",
        "auto", "new", "use", "get", "help", "work", "data",
    }

    tier2 = {
        "meeting", "task", "ticket", "note", "notes", "summary", "chat",
        "email", "code", "copilot", "assistant", "agent", "bot", "workflow",
    }

    t1_terms: List[str] = []
    t2_terms: List[str] = []

    for k in keywords:
        kk = (k or "").strip().lower()
        if not kk or len(kk) < 3 or kk in weak:
            continue
        if kk in tier2:
            t2_terms.append(kk)
        else:
            t1_terms.append(kk)

    selected = (t1_terms[:2] + t2_terms[:1]) if t1_terms else t2_terms[:3]

    if not selected:
        selected = [k.strip().lower() for k in keywords if k.strip()][:2]

    and_query = " ".join([f'"{k}"' if " " in k else k for k in selected])
    return f"{and_query} in:name,description"


# ---------------------------------------------------------------------------
# GitHub search
# ---------------------------------------------------------------------------

def search_github(query: str) -> dict:
    """Search GitHub repositories for the given query string (up to 100 results)."""
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {"q": query, "per_page": 100, "sort": "stars", "order": "desc"}
    resp = requests.get(GITHUB_API_URL, headers=headers, params=params, timeout=10)

    if resp.status_code == 403:
        raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded or bad token.")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="GitHub API error.")

    data = resp.json()
    items = [
        {
            "name": item.get("full_name", ""),
            "description": (item.get("description") or "")[:300],
            "stars": item.get("stargazers_count", 0),
            "url": item.get("html_url", ""),
            "language": item.get("language") or "",
            "fork": item.get("fork", False),
        }
        for item in data.get("items", [])
    ]
    return {"total_count": data.get("total_count", 0), "items": items}


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

# Repos with description shorter than this are considered junk
_JUNK_MIN_DESC_LEN = 20

# match_score >= this threshold counts as a "true competitor"
_HIGH_SIM_THRESHOLD = 3

_STOP_WORDS = {
    "a", "an", "the", "is", "for", "and", "or", "to", "of", "in",
    "that", "with", "into", "from", "as", "at", "by", "on", "it",
    "its", "be", "are", "was", "were", "will", "can", "has", "have",
    "small", "large", "turns", "turn", "make", "makes", "automatically",
    "auto", "using", "used", "uses", "build", "built", "based",
}


def _is_junk_repo(repo: dict) -> bool:
    """Return True if a repo should be discarded (no/trivial description or is a fork)."""
    desc = (repo.get("description") or "").strip()
    if len(desc) < _JUNK_MIN_DESC_LEN:
        return True
    if repo.get("fork", False):
        return True
    return False


def _score_repo(idea_words: List[str], kw_lower: List[str], repo: dict) -> int:
    """Score a single repo against the idea words and keywords.
    
    Scoring:
      +3 per extracted keyword matched (whole-word) in name+description
      +1 per significant idea word matched (whole-word)
    """
    text = (repo.get("name", "") + " " + (repo.get("description") or "")).lower()
    score = 0
    for kw in kw_lower:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            score += 3
    for word in idea_words:
        if re.search(r'\b' + re.escape(word) + r'\b', text):
            score += 1
    return score


def filter_score_repos(idea: str, keywords: List[str], repos: List[dict], display_n: int = 12) -> dict:
    """Filter junk repos, score all remaining by similarity, return ranked results.
    
    Returns:
      top_matches      – top `display_n` repos for UI display (with match_score)
      high_sim_count   – number of repos scoring >= _HIGH_SIM_THRESHOLD (drives risk)
      filtered_count   – total repos after junk removal
      total_scored     – repos with any similarity score ≥ 1
    """
    # Build idea word list (de-duped, no stop words, length > 3)
    seen: set = set()
    idea_words: List[str] = []
    for w in idea.split():
        clean = w.strip(".,!?;:\"'()[]{}").lower()
        if len(clean) > 3 and clean not in _STOP_WORDS and clean not in seen:
            seen.add(clean)
            idea_words.append(clean)

    kw_lower = [k.lower() for k in keywords if k.lower() not in _STOP_WORDS]

    # Step 1: remove junk repos
    clean_repos = [r for r in repos if not _is_junk_repo(r)]
    logger.info(f"GitHub: {len(repos)} fetched → {len(clean_repos)} after junk filter")

    # Step 2: score all clean repos
    scored: List[dict] = []
    for repo in clean_repos:
        s = _score_repo(idea_words, kw_lower, repo)
        if s >= 1:
            scored.append({**repo, "match_score": s})

    # Sort by score desc, then stars desc for tie-breaking
    scored.sort(key=lambda r: (r["match_score"], r.get("stars", 0)), reverse=True)

    # Step 3: cap at 100 after filtering (the "similar github" pool)
    scored = scored[:100]

    high_sim_count = sum(1 for r in scored if r["match_score"] >= _HIGH_SIM_THRESHOLD)
    logger.info(
        f"GitHub: {len(scored)} relevant repos, {high_sim_count} high-similarity (score ≥ {_HIGH_SIM_THRESHOLD})"
    )

    # Top N for display
    display_n = max(5, min(display_n, 15))
    if scored:
        top_matches = scored[:display_n]
    else:
        # Fallback: top repos by stars when nothing matched
        top_matches = sorted(clean_repos, key=lambda r: r.get("stars", 0), reverse=True)[:5]

    return {
        "top_matches": top_matches,
        "high_sim_count": high_sim_count,
        "filtered_count": len(clean_repos),
        "total_scored": len(scored),
    }


def compute_competition_risk(high_sim_count: int) -> float:
    """Map the number of highly-similar repos to a 0–1 competition risk score.
    
    Scale: 0 → 0%, 10 → 40%, 25 → 100%
    """
    return min(high_sim_count / 25.0, 1.0)


def compute_top_matches(idea: str, keywords: List[str], repos: List[dict], top_n: int = 12) -> List[dict]:
    """Convenience wrapper around filter_score_repos for backward compatibility."""
    return filter_score_repos(idea, keywords, repos, display_n=top_n)["top_matches"]


def compute_relevance(keywords: List[str], repos: List[dict]) -> float:
    """Score how relevant the returned repos are to the keywords (0–1)."""
    if not repos:
        return 0.0
    kw_lower = [k.lower() for k in keywords]
    matches = sum(
        1 for repo in repos
        if any(kw in (repo.get("name", "") + " " + (repo.get("description") or "")).lower()
               for kw in kw_lower)
    )
    return matches / len(repos)
