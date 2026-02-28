"""
Prune / PreMortem API
======================
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
# ---------------------------------------------------------------------------

class IdeaRequest(BaseModel):
    idea: str


def get_openai_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key == "your_openai_api_key_here":
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not set. Create a .env file with your key.",
        )
    return key


# ═══════════════════════════════════════════════════════════
# GITHUB ROUTES (from main branch)
# ═══════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════
# REDDIT ROUTES (from reddit-search branch)
# ═══════════════════════════════════════════════════════════

@app.post("/reddit/analyze", response_model=AnalysisResponse)
async def reddit_analyze(input_data: StartupInput):
    """Run Reddit-only agentic signal engine."""
    api_key = get_openai_key()

    try:
        result = await run_reddit_signal_engine(
            openai_api_key=api_key,
            idea=input_data.idea,
            problem=input_data.problem,
            solution=input_data.solution,
            product_specs=input_data.product_specs,
        )
    except Exception as e:
        logger.exception("Reddit engine failed")
        raise HTTPException(status_code=500, detail=str(e))

    threads = [
        SignalThread(**{k: v for k, v in t.items()
                     if k in SignalThread.model_fields})
        for t in result.get("threads", [])
    ]
    scores_raw = result.get("scores", {})
    scores = Scores(**{k: v for k, v in scores_raw.items()
                    if k in Scores.model_fields})

    return AnalysisResponse(
        report=result.get("report", ""),
        scores=scores,
        threads=threads,
        iterations=result.get("iterations", 0),
        queries_used=result.get("queries_used", []),
        coverage=result.get("coverage", {}),
        elapsed_seconds=result.get("elapsed_seconds", 0.0),
    )


# ═══════════════════════════════════════════════════════════
# COMBINED /analyze — GitHub + Reddit together
# ═══════════════════════════════════════════════════════════

@app.post("/analyze")
async def analyze(input_data: StartupInput):
    """Full analysis: GitHub competition + Reddit signals combined."""
    api_key = get_openai_key()

    # --- GitHub signals (sync, fast) ---
    keywords = extract_keywords(input_data.idea)
    query = build_github_query(keywords)
    github_result = search_github(query)
    competition_risk = compute_competition_risk(github_result["total_count"])
    relevance_score = compute_relevance(keywords, github_result["items"])
    top_matches = compute_top_matches(input_data.idea, keywords, github_result["items"])

    github_data = {
        "query": query,
        "keywords": keywords,
        "total_count": github_result["total_count"],
        "competition_risk": competition_risk,
        "relevance_score": relevance_score,
        "repositories": top_matches,
    }

    # --- Reddit signals (async, agentic) ---
    try:
        reddit_result = await run_reddit_signal_engine(
            openai_api_key=api_key,
            idea=input_data.idea,
            problem=input_data.problem,
            solution=input_data.solution,
            product_specs=input_data.product_specs,
        )
    except Exception as e:
        logger.exception("Reddit engine failed during combined analysis")
        reddit_result = {"report": "", "scores": {}, "threads": [], "iterations": 0,
                         "queries_used": [], "coverage": {}, "elapsed_seconds": 0.0}

    threads = [
        SignalThread(**{k: v for k, v in t.items()
                     if k in SignalThread.model_fields})
        for t in reddit_result.get("threads", [])
    ]
    scores_raw = reddit_result.get("scores", {})
    scores = Scores(**{k: v for k, v in scores_raw.items()
                    if k in Scores.model_fields})

    return {
        "idea": input_data.idea,
        "github": github_data,
        "reddit": AnalysisResponse(
            report=reddit_result.get("report", ""),
            scores=scores,
            threads=threads,
            iterations=reddit_result.get("iterations", 0),
            queries_used=reddit_result.get("queries_used", []),
            coverage=reddit_result.get("coverage", {}),
            elapsed_seconds=reddit_result.get("elapsed_seconds", 0.0),
        ),
    }


# ═══════════════════════════════════════════════════════════
# SSE STREAMING — Reddit analysis with live status updates
# ═══════════════════════════════════════════════════════════

@app.post("/analyze/stream")
async def analyze_stream(input_data: StartupInput):
    """SSE streaming: each event is a status update, final event has the result."""
    api_key = get_openai_key()

    async def event_generator() -> AsyncGenerator[str, None]:
        status_queue: asyncio.Queue = asyncio.Queue()

        async def on_status(stage: str, detail: str):
            await status_queue.put({"type": "status", "stage": stage, "detail": detail})

        async def run_engine():
            try:
                result = await run_reddit_signal_engine(
                    openai_api_key=api_key,
                    idea=input_data.idea,
                    problem=input_data.problem,
                    solution=input_data.solution,
                    product_specs=input_data.product_specs,
                    on_status=on_status,
                )
                await status_queue.put({"type": "result", "data": result})
            except Exception as e:
                logger.exception("Engine failed during streaming")
                await status_queue.put({"type": "error", "detail": str(e)})
            finally:
                await status_queue.put(None)

        task = asyncio.create_task(run_engine())

        while True:
            item = await status_queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

        await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# ═══════════════════════════════════════════════════════════
# Health check
# ═══════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {"status": "ok", "engine": "Prune PreMortem v1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
