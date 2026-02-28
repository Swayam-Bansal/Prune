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
    filter_score_repos,
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
    repo_analysis = filter_score_repos(body.idea, keywords, result["items"])
    competition_risk = compute_competition_risk(repo_analysis["high_sim_count"])
    return {
        "query": query,
        "keywords": keywords,
        "total_count": result["total_count"],
        "filtered_count": repo_analysis["filtered_count"],
        "high_sim_count": repo_analysis["high_sim_count"],
        "competition_risk": competition_risk,
        "repositories": repo_analysis["top_matches"],
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


@app.post("/analyze/stream")
async def analyze_stream(body: StartupInput):
    """Streaming analysis pipeline with progress updates."""
    async def event_generator():
        try:
            # Step 1: Extract keywords
            yield f"data: {json.dumps({'step': 0, 'status': 'complete'})}\n\n"
            keywords = extract_keywords(body.idea)
            
            # Step 2: GitHub search
            yield f"data: {json.dumps({'step': 1, 'status': 'complete'})}\n\n"
            query = build_github_query(keywords)
            github_result = search_github(query)
            repo_analysis = filter_score_repos(body.idea, keywords, github_result["items"])
            github_competition_risk = compute_competition_risk(repo_analysis["high_sim_count"])
            github_relevance = repo_analysis["high_sim_count"] / max(repo_analysis["filtered_count"], 1)
            top_repos = repo_analysis["top_matches"]
            
            # Step 3: Web search (Gemini)
            yield f"data: {json.dumps({'step': 2, 'status': 'complete'})}\n\n"
            websearch_data = None
            websearch_competition_risk = 0.0
            try:
                websearch_data = websearch_idea(
                    body.idea,
                    problem=body.problem,
                    solution=body.solution,
                    product_specs=body.product_specs,
                    max_companies=6,
                    max_pages_per_company=4,
                )
                num_companies = len(websearch_data.get("companies", []))
                websearch_competition_risk = min(num_companies / 10.0, 1.0)
            except Exception as e:
                logger.warning(f"WebSearch failed: {e}")
                websearch_data = {"companies": [], "deep_dives": []}
            
            # Step 4: Reddit analysis (only in deep mode)
            reddit_data = None
            reddit_scores = {}
            if body.deep_mode:
                yield f"data: {json.dumps({'step': 3, 'status': 'complete'})}\n\n"
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    try:
                        reddit_data = await run_reddit_signal_engine(
                            openai_api_key=openai_key,
                            idea=body.idea,
                            problem=body.problem,
                            solution=body.solution,
                            product_specs=body.product_specs,
                        )
                        reddit_scores = reddit_data.get("scores", {})
                    except Exception as e:
                        logger.warning(f"Reddit analysis failed: {e}")
                        reddit_data = {"report": "", "scores": {}, "threads": []}
                else:
                    logger.warning("OPENAI_API_KEY not set, skipping Reddit analysis")
                    reddit_data = {"report": "", "scores": {}, "threads": []}
            else:
                logger.info("Skipping Reddit analysis (basic mode)")
                reddit_data = {"report": "", "scores": {}, "threads": []}
                yield f"data: {json.dumps({'step': 3, 'status': 'skipped'})}\n\n"
            
            # Step 5: Compute scores
            final_step = 4 if body.deep_mode else 3
            yield f"data: {json.dumps({'step': final_step, 'status': 'complete'})}\n\n"
            
            # Weighted scoring (adjust weights based on mode)
            if body.deep_mode:
                GITHUB_WEIGHT = 0.30
                WEBSEARCH_WEIGHT = 0.35
                REDDIT_WEIGHT = 0.35
            else:
                # Basic mode: only GitHub + WebSearch
                GITHUB_WEIGHT = 0.45
                WEBSEARCH_WEIGHT = 0.55
                REDDIT_WEIGHT = 0.0
            
            github_score = github_competition_risk * 100
            websearch_score = websearch_competition_risk * 100
            reddit_competition = reddit_scores.get("competition_risk", 50)
            
            combined_competition_risk = (
                github_score * GITHUB_WEIGHT +
                websearch_score * WEBSEARCH_WEIGHT +
                reddit_competition * REDDIT_WEIGHT
            )
            
            demand_score = reddit_scores.get("demand_score", 50)
            pain_validation = reddit_scores.get("pain_validation", 50)
            
            overall_failure_probability = (
                combined_competition_risk * 0.4 +
                (100 - demand_score) * 0.35 +
                (100 - pain_validation) * 0.25
            )
            
            # Send final result
            result = {
                "idea": body.idea,
                "keywords": keywords,
                "scores": {
                    "competition_risk": round(combined_competition_risk, 1),
                    "demand_score": round(demand_score, 1),
                    "pain_validation": round(pain_validation, 1),
                    "overall_failure_probability": round(overall_failure_probability, 1),
                    "breakdown": {
                        "github_competition": round(github_score, 1),
                        "websearch_competition": round(websearch_score, 1),
                        "reddit_competition": round(reddit_competition, 1),
                    },
                },
                "github": {
                    "query": query,
                    "total_count": github_result["total_count"],
                    "filtered_count": repo_analysis["filtered_count"],
                    "high_sim_count": repo_analysis["high_sim_count"],
                    "competition_risk": github_competition_risk,
                    "relevance_score": round(github_relevance, 3),
                    "repositories": top_repos,
                },
                "websearch": {
                    "companies": websearch_data.get("companies", []),
                    "deep_dives": websearch_data.get("deep_dives", []),
                    "num_companies_found": len(websearch_data.get("companies", [])),
                },
                "reddit": {
                    "report": reddit_data.get("report", ""),
                    "threads": reddit_data.get("threads", []),
                    "iterations": reddit_data.get("iterations", 0),
                    "coverage": reddit_data.get("coverage", {}),
                },
                "weights": {
                    "github": GITHUB_WEIGHT,
                    "websearch": WEBSEARCH_WEIGHT,
                    "reddit": REDDIT_WEIGHT,
                },
            }
            
            yield f"data: {json.dumps({'step': 'done', 'result': result})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/analyze")
async def analyze(body: StartupInput):
    """Full analysis pipeline: GitHub + WebSearch + Reddit with weighted scoring."""
    # === GITHUB ANALYSIS ===
    keywords = extract_keywords(body.idea)
    query = build_github_query(keywords)
    github_result = search_github(query)
    repo_analysis = filter_score_repos(body.idea, keywords, github_result["items"])
    github_competition_risk = compute_competition_risk(repo_analysis["high_sim_count"])
    github_relevance = repo_analysis["high_sim_count"] / max(repo_analysis["filtered_count"], 1)
    top_repos = repo_analysis["top_matches"]
    
    # === WEB SEARCH ANALYSIS ===
    websearch_data = None
    websearch_competition_risk = 0.0
    try:
        websearch_data = websearch_idea(
            body.idea,
            problem=body.problem,
            solution=body.solution,
            product_specs=body.product_specs,
            max_companies=6,
            max_pages_per_company=4,
        )
        # Calculate competition risk from number of similar companies found
        num_companies = len(websearch_data.get("companies", []))
        websearch_competition_risk = min(num_companies / 10.0, 1.0)  # 10+ companies = max risk
    except Exception as e:
        logger.warning(f"WebSearch failed: {e}")
        websearch_data = {"companies": [], "deep_dives": []}
    
    # === REDDIT ANALYSIS (only in deep mode) ===
    reddit_data = None
    reddit_scores = {}
    if body.deep_mode:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                reddit_data = await run_reddit_signal_engine(
                    openai_api_key=openai_key,
                    idea=body.idea,
                    problem=body.problem,
                    solution=body.solution,
                    product_specs=body.product_specs,
                )
                reddit_scores = reddit_data.get("scores", {})
            except Exception as e:
                logger.warning(f"Reddit analysis failed: {e}")
                reddit_data = {"report": "", "scores": {}, "threads": []}
        else:
            logger.warning("OPENAI_API_KEY not set, skipping Reddit analysis")
            reddit_data = {"report": "", "scores": {}, "threads": []}
    else:
        logger.info("Skipping Reddit analysis (basic mode)")
        reddit_data = {"report": "", "scores": {}, "threads": []}
    
    # === WEIGHTED SCORING SYSTEM ===
    # Weights adjust based on mode
    if body.deep_mode:
        # Deep mode: GitHub 30%, WebSearch 35%, Reddit 35%
        GITHUB_WEIGHT = 0.30
        WEBSEARCH_WEIGHT = 0.35
        REDDIT_WEIGHT = 0.35
    else:
        # Basic mode: GitHub 45%, WebSearch 55%
        GITHUB_WEIGHT = 0.45
        WEBSEARCH_WEIGHT = 0.55
        REDDIT_WEIGHT = 0.0
    
    # Normalize scores to 0-100 scale
    github_score = github_competition_risk * 100  # Already 0-1
    websearch_score = websearch_competition_risk * 100  # Already 0-1
    reddit_competition = reddit_scores.get("competition_risk", 50)  # Assume 0-100
    
    # Combined competition risk (0-100)
    combined_competition_risk = (
        github_score * GITHUB_WEIGHT +
        websearch_score * WEBSEARCH_WEIGHT +
        reddit_competition * REDDIT_WEIGHT
    )
    
    # Demand score (primarily from Reddit)
    demand_score = reddit_scores.get("demand_score", 50)
    
    # Pain validation (primarily from Reddit)
    pain_validation = reddit_scores.get("pain_validation", 50)
    
    # Overall failure probability calculation
    # High competition + Low demand + Low pain = High failure risk
    overall_failure_probability = (
        combined_competition_risk * 0.4 +  # 40% weight on competition
        (100 - demand_score) * 0.35 +       # 35% weight on lack of demand
        (100 - pain_validation) * 0.25      # 25% weight on lack of pain validation
    )
    
    return {
        "idea": body.idea,
        "keywords": keywords,
        "scores": {
            "competition_risk": round(combined_competition_risk, 1),
            "demand_score": round(demand_score, 1),
            "pain_validation": round(pain_validation, 1),
            "overall_failure_probability": round(overall_failure_probability, 1),
            "breakdown": {
                "github_competition": round(github_score, 1),
                "websearch_competition": round(websearch_score, 1),
                "reddit_competition": round(reddit_competition, 1),
            },
        },
        "github": {
            "query": query,
            "total_count": github_result["total_count"],
            "filtered_count": repo_analysis["filtered_count"],
            "high_sim_count": repo_analysis["high_sim_count"],
            "competition_risk": github_competition_risk,
            "relevance_score": round(github_relevance, 3),
            "repositories": top_repos,
        },
        "websearch": {
            "companies": websearch_data.get("companies", []),
            "deep_dives": websearch_data.get("deep_dives", []),
            "num_companies_found": len(websearch_data.get("companies", [])),
        },
        "reddit": {
            "report": reddit_data.get("report", ""),
            "threads": reddit_data.get("threads", []),
            "iterations": reddit_data.get("iterations", 0),
            "coverage": reddit_data.get("coverage", {}),
        },
        "weights": {
            "github": GITHUB_WEIGHT,
            "websearch": WEBSEARCH_WEIGHT,
            "reddit": REDDIT_WEIGHT,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
