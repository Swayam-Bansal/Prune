"""
Agentic Reddit Signal Engine
=============================
Implements a multi-stage feedback loop:

  1. GENERATE  — ChatGPT creates smart search queries from user input
  2. SEARCH    — Reddit API retrieves threads for each query
  3. ANALYZE   — ChatGPT scores and classifies every thread
  4. EVALUATE  — Check signal coverage; if gaps exist, go to step 5
  5. REFINE    — ChatGPT generates new queries to fill gaps → back to step 2
  6. SYNTHESIZE — ChatGPT writes the final market signal report

The loop runs up to MAX_ITERATIONS times (default 3).
"""

import json
import logging
import time
from typing import Any

from openai import AsyncOpenAI

from prompts import (
    QUERY_GENERATION_SYSTEM,
    QUERY_GENERATION_USER,
    ANALYSIS_SYSTEM,
    ANALYSIS_USER,
    REFINEMENT_SYSTEM,
    REFINEMENT_USER,
    SYNTHESIS_SYSTEM,
    SYNTHESIS_USER,
)
from reddit_client import search_reddit, fetch_thread_comments

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────
MAX_ITERATIONS = 3          # max feedback-loop cycles
INITIAL_QUERIES = 6         # queries generated in round 1
REFINEMENT_QUERIES = 4      # queries generated per refinement round
MIN_SIGNALS_PER_TYPE = 2    # minimum threads needed per signal type before we stop
MODEL = "gpt-4o"            # model to use
TEMPERATURE = 0.4           # low temp for structured output


async def call_openai(
    client: AsyncOpenAI,
    system: str,
    user: str,
    temperature: float = TEMPERATURE,
) -> str:
    """Call OpenAI ChatCompletion and return the assistant message content."""
    response = await client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def safe_parse_json(raw: str) -> Any:
    """Parse JSON from ChatGPT, handling common quirks."""
    raw = raw.strip()
    # Sometimes the model wraps in ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
    try:
        parsed = json.loads(raw)
        # If the model returned {"queries": [...]}, unwrap
        if isinstance(parsed, dict):
            for key in ("queries", "results", "threads", "signals", "data"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nRaw: {raw[:500]}")
        return []


# ─────────────────────────────────────────────────────────
# Stage 1: Generate Search Queries
# ─────────────────────────────────────────────────────────
async def generate_queries(
    client: AsyncOpenAI,
    idea: str,
    problem: str,
    solution: str,
    product_specs: str,
    num_queries: int = INITIAL_QUERIES,
) -> list[dict]:
    """Use ChatGPT to generate Reddit search queries from user input."""
    user_prompt = QUERY_GENERATION_USER.format(
        idea=idea,
        problem=problem,
        solution=solution,
        product_specs=product_specs,
        num_queries=num_queries,
    )
    raw = await call_openai(client, QUERY_GENERATION_SYSTEM, user_prompt)
    queries = await safe_parse_json(raw)

    if not isinstance(queries, list):
        logger.error(f"Expected list of queries, got: {type(queries)}")
        return []

    logger.info(f"Generated {len(queries)} search queries")
    return queries


# ─────────────────────────────────────────────────────────
# Stage 2: Search Reddit
# ─────────────────────────────────────────────────────────
async def search_all_queries(queries: list[dict]) -> dict[str, list[dict]]:
    """
    Run all search queries against Reddit.
    Returns a dict mapping query_string -> list of threads.
    """
    results = {}
    for q in queries:
        query_str = q.get("query", "")
        subreddits = q.get("subreddits", [])
        if not query_str:
            continue

        threads = await search_reddit(
            query=query_str,
            subreddits=subreddits,
            limit=10,
            sort="relevance",
            time_filter="all",
        )

        # For top threads (high score), also fetch comments for richer signal
        enriched_threads = []
        for thread in threads:
            if thread["num_comments"] >= 5 and thread["score"] >= 10:
                comments = await fetch_thread_comments(thread["url"], limit=5)
                thread["top_comments"] = comments
            else:
                thread["top_comments"] = []
            enriched_threads.append(thread)

        results[query_str] = enriched_threads
        logger.info(f"Query '{query_str}' → {len(enriched_threads)} threads")

    return results


# ─────────────────────────────────────────────────────────
# Stage 3: Analyze Threads
# ─────────────────────────────────────────────────────────
async def analyze_threads(
    client: AsyncOpenAI,
    idea: str,
    problem: str,
    solution: str,
    product_specs: str,
    query: str,
    intent: str,
    threads: list[dict],
) -> list[dict]:
    """Use ChatGPT to score and classify each thread's relevance."""
    if not threads:
        return []

    # Prepare a concise representation of threads for the prompt
    threads_for_prompt = []
    for t in threads:
        threads_for_prompt.append({
            "id": t["id"],
            "title": t["title"],
            "selftext": t["selftext"][:800],
            "subreddit": t["subreddit"],
            "score": t["score"],
            "num_comments": t["num_comments"],
            "top_comments": t.get("top_comments", [])[:3],
        })

    user_prompt = ANALYSIS_USER.format(
        idea=idea,
        problem=problem,
        solution=solution,
        product_specs=product_specs,
        query=query,
        intent=intent,
        threads_json=json.dumps(threads_for_prompt, indent=2),
    )
    raw = await call_openai(client, ANALYSIS_SYSTEM, user_prompt)
    analyzed = await safe_parse_json(raw)

    if not isinstance(analyzed, list):
        logger.error(
            f"Expected list of analyzed threads, got: {type(analyzed)}")
        return []

    # Merge analysis back with original thread data
    thread_map = {t["id"]: t for t in threads}
    enriched = []
    for a in analyzed:
        tid = a.get("thread_id", "")
        original = thread_map.get(tid, {})
        enriched.append({
            **a,
            "title": original.get("title", ""),
            "url": original.get("url", ""),
            "subreddit": original.get("subreddit", ""),
            "score": original.get("score", 0),
            "num_comments": original.get("num_comments", 0),
            "source_query": query,
        })

    logger.info(f"Analyzed {len(enriched)} threads for query '{query}'")
    return enriched


# ─────────────────────────────────────────────────────────
# Stage 4: Evaluate Signal Coverage
# ─────────────────────────────────────────────────────────
def evaluate_coverage(all_signals: list[dict]) -> dict:
    """
    Count signals by type and identify gaps.
    Returns a coverage report.
    """
    counts = {
        "pain_point": 0,
        "competition": 0,
        "demand": 0,
        "skepticism": 0,
    }
    competitors = set()

    for s in all_signals:
        st = s.get("signal_type", "irrelevant")
        if st in counts:
            counts[st] += 1
        for prod in s.get("competing_products", []):
            competitors.add(prod)

    gaps = []
    for signal_type, count in counts.items():
        if count < MIN_SIGNALS_PER_TYPE:
            gaps.append(
                f"{signal_type} ({count} found, need {MIN_SIGNALS_PER_TYPE})")

    has_gaps = len(gaps) > 0

    return {
        "counts": counts,
        "competitors": list(competitors),
        "gaps": gaps,
        "has_gaps": has_gaps,
    }


# ─────────────────────────────────────────────────────────
# Stage 5: Refine Queries (Feedback Loop)
# ─────────────────────────────────────────────────────────
async def refine_queries(
    client: AsyncOpenAI,
    idea: str,
    problem: str,
    solution: str,
    product_specs: str,
    coverage: dict,
    total_threads: int,
) -> list[dict]:
    """Use ChatGPT to generate refined queries based on coverage gaps."""
    user_prompt = REFINEMENT_USER.format(
        idea=idea,
        problem=problem,
        solution=solution,
        product_specs=product_specs,
        total_threads=total_threads,
        pain_count=coverage["counts"]["pain_point"],
        comp_count=coverage["counts"]["competition"],
        demand_count=coverage["counts"]["demand"],
        skepticism_count=coverage["counts"]["skepticism"],
        competitors=", ".join(
            coverage["competitors"][:10]) or "None found yet",
        gaps="; ".join(coverage["gaps"]) or "None",
        num_queries=REFINEMENT_QUERIES,
    )
    raw = await call_openai(client, REFINEMENT_SYSTEM, user_prompt)
    queries = await safe_parse_json(raw)

    if not isinstance(queries, list):
        return []

    logger.info(f"Refinement generated {len(queries)} new queries")
    return queries


# ─────────────────────────────────────────────────────────
# Stage 6: Synthesize Final Report
# ─────────────────────────────────────────────────────────
async def synthesize_report(
    client: AsyncOpenAI,
    idea: str,
    problem: str,
    solution: str,
    product_specs: str,
    all_signals: list[dict],
) -> dict:
    """Use ChatGPT to write the final market signal report."""
    # Only include the most relevant signals for the synthesis prompt
    top_signals = sorted(
        all_signals,
        key=lambda s: s.get("relevance_score", 0),
        reverse=True,
    )[:30]  # cap to avoid token overflow

    user_prompt = SYNTHESIS_USER.format(
        idea=idea,
        problem=problem,
        solution=solution,
        product_specs=product_specs,
        all_signals_json=json.dumps(top_signals, indent=2),
    )
    raw = await call_openai(client, SYNTHESIS_SYSTEM, user_prompt, temperature=0.5)
    parsed = await safe_parse_json(raw)

    if isinstance(parsed, dict):
        return parsed
    return {"report": str(parsed), "scores": {}}


# ─────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR — The Agentic Loop
# ─────────────────────────────────────────────────────────
async def run_reddit_signal_engine(
    openai_api_key: str,
    idea: str,
    problem: str,
    solution: str,
    product_specs: str,
    on_status: callable = None,
) -> dict:
    """
    Main entry point. Runs the full agentic loop:
      Generate → Search → Analyze → Evaluate → (Refine → Search → Analyze)* → Synthesize

    Parameters:
      on_status: optional async callback(stage: str, detail: str) for streaming status updates

    Returns a dict with:
      - report: str (markdown)
      - scores: dict
      - threads: list[dict] (all analyzed threads)
      - iterations: int
      - coverage: dict
    """
    client = AsyncOpenAI(api_key=openai_api_key)
    all_signals: list[dict] = []
    all_queries_used: list[str] = []
    iteration = 0
    start_time = time.time()

    async def status(stage: str, detail: str):
        if on_status:
            await on_status(stage, detail)
        logger.info(f"[{stage}] {detail}")

    # ── ITERATION LOOP ──
    while iteration < MAX_ITERATIONS:
        iteration += 1
        await status("iteration", f"Starting iteration {iteration}/{MAX_ITERATIONS}")

        # Step 1: Generate or Refine queries
        if iteration == 1:
            await status("generating_queries", "Generating initial search queries...")
            queries = await generate_queries(
                client, idea, problem, solution, product_specs, INITIAL_QUERIES
            )
        else:
            await status("refining_queries", f"Refining queries (iteration {iteration})...")
            coverage = evaluate_coverage(all_signals)
            if not coverage["has_gaps"]:
                await status("coverage_complete", "All signal types have sufficient coverage!")
                break
            queries = await refine_queries(
                client, idea, problem, solution, product_specs,
                coverage, len(all_signals),
            )

        if not queries:
            await status("warning", "No queries generated, stopping loop.")
            break

        # Step 2: Search Reddit
        await status("searching", f"Searching Reddit with {len(queries)} queries...")
        search_results = await search_all_queries(queries)

        # Step 3: Analyze each batch of threads
        for q in queries:
            query_str = q.get("query", "")
            intent = q.get("intent", "demand")
            threads = search_results.get(query_str, [])

            if not threads:
                continue

            all_queries_used.append(query_str)
            await status("analyzing", f"Analyzing {len(threads)} threads for: '{query_str}'")

            analyzed = await analyze_threads(
                client, idea, problem, solution, product_specs,
                query_str, intent, threads,
            )
            all_signals.extend(analyzed)

        # Step 4: Evaluate coverage
        coverage = evaluate_coverage(all_signals)
        await status(
            "evaluation",
            f"Signals: pain={coverage['counts']['pain_point']}, "
            f"comp={coverage['counts']['competition']}, "
            f"demand={coverage['counts']['demand']}, "
            f"skepticism={coverage['counts']['skepticism']} | "
            f"Gaps: {len(coverage['gaps'])}",
        )

        # If no gaps, we're done
        if not coverage["has_gaps"]:
            break

    # ── DEDUPLICATE signals by thread_id ──
    seen_ids = set()
    unique_signals = []
    for s in all_signals:
        tid = s.get("thread_id", "")
        if tid and tid not in seen_ids:
            seen_ids.add(tid)
            unique_signals.append(s)
    all_signals = unique_signals

    # ── SYNTHESIZE ──
    await status("synthesizing", f"Synthesizing report from {len(all_signals)} signals...")
    report_data = await synthesize_report(
        client, idea, problem, solution, product_specs, all_signals
    )

    elapsed = round(time.time() - start_time, 1)
    await status("complete", f"Done in {elapsed}s — {iteration} iterations, {len(all_signals)} signals")

    final_coverage = evaluate_coverage(all_signals)

    return {
        "report": report_data.get("report", ""),
        "scores": report_data.get("scores", {}),
        "threads": sorted(
            all_signals,
            key=lambda s: s.get("relevance_score", 0),
            reverse=True,
        ),
        "iterations": iteration,
        "queries_used": all_queries_used,
        "coverage": final_coverage,
        "elapsed_seconds": elapsed,
    }
