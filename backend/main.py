"""
PreMortem API — Agentic Reddit Signal Engine
=============================================
FastAPI server with:
  - POST /analyze         → full synchronous analysis
  - POST /analyze/stream  → SSE streaming with live status updates

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

from engine import run_reddit_signal_engine
from models import AnalysisResponse, Scores, SignalThread, StartupInput

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PreMortem — Reddit Signal Engine",
    description="Agentic market research using Reddit signals + ChatGPT",
    version="1.0.0",
)

# CORS — allow the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_openai_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key == "your_openai_api_key_here":
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not set. Create a .env file with your key.",
        )
    return key


# ─────────────────────────────────────────────────────────
# POST /analyze — Synchronous full analysis
# ─────────────────────────────────────────────────────────
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(input_data: StartupInput):
    """Run the full agentic Reddit signal engine and return the complete result."""
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
        logger.exception("Engine failed")
        raise HTTPException(status_code=500, detail=str(e))

    # Build typed response
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


# ─────────────────────────────────────────────────────────
# POST /analyze/stream — SSE streaming with status updates
# ─────────────────────────────────────────────────────────
@app.post("/analyze/stream")
async def analyze_stream(input_data: StartupInput):
    """
    Run the engine with Server-Sent Events.
    Each event is a JSON status update, and the final event contains the full result.
    """
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
                await status_queue.put(None)  # sentinel

        # Start engine in background
        task = asyncio.create_task(run_engine())

        while True:
            item = await status_queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

        await task  # ensure it's done

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ─────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "engine": "PreMortem Reddit Signal Engine v1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
