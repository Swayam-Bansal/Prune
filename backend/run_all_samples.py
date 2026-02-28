"""
Run all SAMPLE_INPUTS through the /analyze endpoint and save results to CSV.
Usage:
    python run_all_samples.py
"""

import csv
import json
import time
import httpx
from mock_data import SAMPLE_INPUTS

API_URL = "http://127.0.0.1:8000/analyze"
OUTPUT_CSV = "results.csv"
TIMEOUT = 600  # 10 minutes per request (real analysis takes 3-5 min)


def run_analysis(input_data: dict) -> dict:
    """Send a single startup idea to /analyze and return the JSON response."""
    print(f"\n{'='*60}")
    print(f"  Analyzing: {input_data['idea']}")
    print(f"{'='*60}")
    start = time.time()

    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(API_URL, json=input_data)
        resp.raise_for_status()

    elapsed = time.time() - start
    result = resp.json()
    print(f"  ✅ Done in {elapsed:.1f}s — {result.get('iterations', '?')} iterations, "
          f"{len(result.get('threads', []))} threads analyzed")
    return result


def flatten_to_row(input_data: dict, result: dict) -> dict:
    """Flatten the nested JSON response into a single CSV row."""
    scores = result.get("scores", {})
    coverage = result.get("coverage", {})
    counts = coverage.get("counts", {})
    threads = result.get("threads", [])

    # Extract top 5 threads by relevance
    top_threads = sorted(threads, key=lambda t: t.get("relevance_score", 0), reverse=True)[:5]
    top_thread_summaries = []
    for t in top_threads:
        title = t.get("title", "")[:80]
        score = t.get("relevance_score", 0)
        signal = t.get("signal_type", "")
        top_thread_summaries.append(f"[{signal}|{score}] {title}")

    # Extract all competitors
    all_competitors = set()
    for t in threads:
        for c in t.get("competing_products", []):
            all_competitors.add(c)

    # Extract all unmet needs
    all_unmet = set()
    for t in threads:
        for u in t.get("unmet_needs", []):
            all_unmet.add(u)

    # Extract report recommendation (last paragraph or section 7)
    report = result.get("report", "")
    # Try to find the recommendation keyword
    recommendation = ""
    for line in report.split("\n"):
        line_lower = line.strip().lower()
        if any(word in line_lower for word in ["recommendation", "**go", "**pivot", "**kill", "**stop"]):
            recommendation = line.strip()
            if recommendation:
                break

    return {
        "idea": input_data["idea"],
        "problem": input_data["problem"],
        "solution": input_data["solution"],
        "product_specs": input_data["product_specs"],
        "demand_score": scores.get("demand_score", ""),
        "competition_risk": scores.get("competition_risk", ""),
        "pain_validation": scores.get("pain_validation", ""),
        "overall_failure_probability": scores.get("overall_failure_probability", ""),
        "recommendation": recommendation,
        "iterations": result.get("iterations", ""),
        "total_threads_analyzed": len(threads),
        "pain_point_signals": counts.get("pain_point", 0),
        "demand_signals": counts.get("demand", 0),
        "competition_signals": counts.get("competition", 0),
        "skepticism_signals": counts.get("skepticism", 0),
        "competitors_found": "; ".join(sorted(all_competitors)),
        "unmet_needs": "; ".join(sorted(all_unmet)),
        "top_threads": " || ".join(top_thread_summaries),
        "queries_used": "; ".join(result.get("queries_used", [])),
        "elapsed_seconds": result.get("elapsed_seconds", ""),
        "full_report": report,
    }


def main():
    print(f"\n🚀 PreMortem Batch Runner — analyzing {len(SAMPLE_INPUTS)} startup ideas")
    print(f"   Results will be saved to: {OUTPUT_CSV}\n")

    rows = []
    for i, input_data in enumerate(SAMPLE_INPUTS, 1):
        print(f"\n[{i}/{len(SAMPLE_INPUTS)}]", end="")
        try:
            result = run_analysis(input_data)
            row = flatten_to_row(input_data, result)
            rows.append(row)
        except httpx.HTTPStatusError as e:
            print(f"  ❌ HTTP error: {e.response.status_code} — {e.response.text[:200]}")
            rows.append({"idea": input_data["idea"], "error": str(e)})
        except httpx.ConnectError:
            print(f"  ❌ Connection error — is the server running on {API_URL}?")
            rows.append({"idea": input_data["idea"], "error": "Connection refused"})
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            rows.append({"idea": input_data["idea"], "error": str(e)})

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        # Ensure all rows have the same keys
        all_keys = set()
        for r in rows:
            all_keys.update(r.keys())
        fieldnames = sorted(all_keys)

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        print(f"\n{'='*60}")
        print(f"  ✅ Results saved to {OUTPUT_CSV}")
        print(f"  📊 {len(rows)} ideas analyzed")
        print(f"{'='*60}\n")

        # Also print a summary table
        print(f"\n{'Idea':<50} {'Demand':>7} {'Pain':>7} {'Comp':>7} {'Fail%':>7} {'Threads':>8}")
        print("-" * 95)
        for row in rows:
            if "error" in row and row.get("demand_score", "") == "":
                print(f"{row.get('idea', '???'):<50} {'ERROR':>7}")
            else:
                print(f"{row.get('idea', '???')[:48]:<50} "
                      f"{row.get('demand_score', '?'):>7} "
                      f"{row.get('pain_validation', '?'):>7} "
                      f"{row.get('competition_risk', '?'):>7} "
                      f"{row.get('overall_failure_probability', '?'):>7} "
                      f"{row.get('total_threads_analyzed', '?'):>8}")
    else:
        print("\n❌ No results to save.")


if __name__ == "__main__":
    main()
