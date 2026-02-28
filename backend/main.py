Unified FastAPI server combining:
  • GitHub competition signals   (from main branch)
  • Agentic Reddit signal engine (from reddit-search branch)

Routes:
  POST /github/search          → GitHub competition search
  POST /analyze                → Full analysis (GitHub + Reddit)
  POST /analyze/stream         → SSE streaming Reddit analysis
  POST /reddit/analyze         → Reddit-only analysis
  GET  /health

Run with:
  uvicorn main:app --reload --port 8000
"""

import asyncio
import json
import logging
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from engine import run_reddit_signal_engine
from github_client import (
    build_github_query,
    compute_competition_risk,
    compute_relevance,
    compute_top_matches,
    extract_keywords,
    search_github,
)
from models import AnalysisResponse, Scores, SignalThread, StartupInput

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Prune — PreMortem Market Signal Engine",
    description="GitHub competition signals + Agentic Reddit signal analysis",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
import logging
import os
from typing import List

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Prune – GitHub Competition Signal API")

GITHUB_API_URL = "https://api.github.com/search/repositories"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class IdeaRequest(BaseModel):
    idea: str


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def extract_keywords(text: str) -> List[str]:
    """Extract core keywords from an idea string.

    Uses Gemini when GEMINI_API_KEY is set; otherwise falls back to the first
    five non-trivial words of the input (deterministic, no network required).
    """
    if os.getenv("GEMINI_API_KEY"):
        try:
            import json

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
                import re
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


def build_github_query(keywords: List[str]) -> str:
    """Build a GitHub search query from extracted keywords.

    Strategy:
    - Discard generic/weak words entirely.
    - Tier remaining keywords by specificity: product/platform names and
      technical jargon (tier 1) beat broad domain nouns like 'meeting' or
      'copilot' (tier 2). Always prefer tier-1 terms first.
    - Use AND semantics with 2-3 terms; more terms = fewer but cleaner results.
    - Restrict to name/description to avoid README noise.
    """
    # Words that produce extremely broad or irrelevant GitHub results
    weak = {
        "ai", "automatically", "turn", "turns", "build", "building",
        "make", "makes", "small", "large", "simple", "easy", "quick",
        "app", "tool", "platform", "system", "using", "based", "create",
        "auto", "new", "use", "get", "help", "work", "data",
    }

    # Generic but still searchable domain words — use only if nothing better
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

    # Build query: prefer t1 terms; supplement with t2 only if we need more
    selected = (t1_terms[:2] + t2_terms[:1]) if t1_terms else t2_terms[:3]

    if not selected:
        # Last resort: anything non-empty
        selected = [k.strip().lower() for k in keywords if k.strip()][:2]

    and_query = " ".join([f'"{k}"' if " " in k else k for k in selected])
    return f"{and_query} in:name,description"


def search_github(query: str) -> dict:
    """Search GitHub repositories for the given query string.

    Returns a dict with ``total_count`` (int) and ``items`` (list of repo dicts
    with at least ``name`` and ``description`` keys).
    """
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {"q": query, "per_page": 30, "sort": "stars", "order": "desc"}
    resp = requests.get(GITHUB_API_URL, headers=headers, params=params, timeout=10)

    if resp.status_code == 403:
        raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded or bad token.")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="GitHub API error.")

    data = resp.json()
    items = [
        {
            "name": item.get("full_name", ""),
            "description": (item.get("description") or "")[:200],  # Truncate to 200 chars
            "stars": item.get("stargazers_count", 0),
            "url": item.get("html_url", ""),
            "language": item.get("language") or "",
        }
        for item in data.get("items", [])
    ]
    return {"total_count": data.get("total_count", 0), "items": items}


def compute_competition_risk(total_count: int) -> float:
    """Map a GitHub repository count to a 0–1 competition risk score.

    Linearly scales 0 → 0.0 and 100 → 1.0, capped at 1.0.
    """
    return min(total_count / 100.0, 1.0)


def compute_top_matches(idea: str, keywords: List[str], repos: List[dict], top_n: int = 10) -> List[dict]:
    """Re-rank repos by similarity to the original idea and return the top N.

    Scoring (per repo, higher = more similar):
    - +3 per keyword matched as a whole word in name or description
    - +1 per meaningful word from the full idea matched as a whole word
    Whole-word matching prevents substring false positives (e.g. 'small' in
    'too small to get its fat little body'). Repos must score >= 2 to qualify.
    Result capped at top_n (max 10, min 5).
    """
    import re

    stop_words = {
        "a", "an", "the", "is", "for", "and", "or", "to", "of", "in",
        "that", "with", "into", "from", "as", "at", "by", "on", "it",
        "its", "be", "are", "was", "were", "will", "can", "has", "have",
        "small", "large", "turns", "turn", "make", "makes", "automatically",
        "auto", "using", "used", "uses", "build", "built", "based",
    }

    def whole_word_match(word: str, text: str) -> bool:
        return bool(re.search(r'\b' + re.escape(word) + r'\b', text))

    # Deduplicated meaningful words from the full idea
    seen: set = set()
    idea_words: List[str] = []
    for w in idea.split():
        clean = w.strip(".,!?;:\"'()[]{}").lower()
        if len(clean) > 3 and clean not in stop_words and clean not in seen:
            seen.add(clean)
            idea_words.append(clean)

    kw_lower = [k.lower() for k in keywords if k.lower() not in stop_words]

    scored: List[dict] = []
    for repo in repos:
        text = (repo.get("name", "") + " " + (repo.get("description") or "")).lower()
        score = 0
        for kw in kw_lower:
            if whole_word_match(kw, text):
                score += 3
        for word in idea_words:
            if whole_word_match(word, text):
                score += 1
        if score >= 2:
            scored.append({**repo, "match_score": score})

    scored.sort(key=lambda r: r["match_score"], reverse=True)
    top_n = max(5, min(top_n, 10))
    return scored[:top_n]


def compute_relevance(keywords: List[str], repos: List[dict]) -> float:
    """Score how relevant the returned repos are to the keywords.

    For each repo, checks whether ANY keyword appears in its name or
    description. Returns the fraction of repos that match at least one keyword.
    Returns 0.0 if repos is empty.
    """
    if not repos:
        return 0.0

    kw_lower = [k.lower() for k in keywords]
    matches = 0
    for repo in repos:
        text = (repo.get("name", "") + " " + (repo.get("description") or "")).lower()
        if any(kw in text for kw in kw_lower):
            matches += 1

    return matches / len(repos)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/github/search")
def github_search(body: IdeaRequest):
    """Search GitHub directly for the raw idea string."""
    keywords = extract_keywords(body.idea)
    query = build_github_query(keywords)
    result = search_github(query)
    competition_risk = compute_competition_risk(result["total_count"])
    relevance_score = compute_relevance(keywords, result["items"])
    top_matches = compute_top_matches(body.idea, keywords, result["items"])
    return {
        "query": query,
        "keywords": keywords,
        "total_count": result["total_count"],
        "competition_risk": competition_risk,
        "relevance_score": relevance_score,
        "repositories": top_matches,
    }


@app.post("/analyze")
def analyze(body: IdeaRequest):
    """Full analysis pipeline: extract keywords → GitHub search → score."""
    keywords = extract_keywords(body.idea)
    query = build_github_query(keywords)
    github_result = search_github(query)

    competition_risk = compute_competition_risk(github_result["total_count"])
    relevance_score = compute_relevance(keywords, github_result["items"])

    top_matches = compute_top_matches(body.idea, keywords, github_result["items"])
    return {
        "idea": body.idea,
        "keywords": keywords,
        "github": {
            "query": query,
            "total_count": github_result["total_count"],
            "competition_risk": competition_risk,
            "relevance_score": relevance_score,
            "repositories": top_matches,
        },
    }
