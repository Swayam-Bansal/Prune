"""
Unified FastAPI server combining:
  • GitHub competition signals
  • Web search for competitive companies
  • Agentic Reddit signal engine

Routes:
  POST /github/search          → GitHub competition search
  POST /websearch              → Web search for competitive companies
  POST /analyze                → Full analysis (GitHub + Reddit)
  POST /analyze/stream         → SSE streaming Reddit analysis
  POST /reddit/analyze         → Reddit-only analysis
  GET  /health
  GET  /debug/env              → Debug environment variables

Run with:
  uvicorn main:app --reload --port 8000
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import AsyncGenerator, List

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

try:
    _root_env = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=_root_env, override=False)
except Exception:
    load_dotenv()

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
from websearch import WebSearchError, websearch_idea

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Prune — PreMortem Market Signal Engine",
    description="GitHub competition signals + Web search + Agentic Reddit signal analysis",
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

GITHUB_API_URL = "https://api.github.com/search/repositories"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class IdeaRequest(BaseModel):
    idea: str


class WebSearchRequest(BaseModel):
    idea: str = Field(..., min_length=1)
    problem: str = ""
    solution: str = ""
    product_specs: str = ""
    max_companies: int = Field(6, ge=1, le=20)
    max_pages_per_company: int = Field(4, ge=1, le=10)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/env")
def debug_env() -> dict:
    try:
        env_path = str(Path(__file__).resolve().parents[1] / ".env")
        env_exists = Path(env_path).exists()
    except Exception:
        env_path = None
        env_exists = None

    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_google = bool(os.getenv("GOOGLE_API_KEY"))
    has_github = bool(os.getenv("GITHUB_TOKEN"))
    return {
        "env_path": env_path,
        "env_exists": env_exists,
        "has_gemini_api_key": has_gemini,
        "has_google_api_key": has_google,
        "has_github_token": has_github,
    }


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


@app.post("/websearch")
def websearch(req: WebSearchRequest) -> dict:
    """Web search for competitive companies."""
    try:
        return websearch_idea(
            req.idea,
            problem=req.problem,
            solution=req.solution,
            product_specs=req.product_specs,
            max_companies=req.max_companies,
            max_pages_per_company=req.max_pages_per_company,
        )
    except WebSearchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"websearch failed: {e}")


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
