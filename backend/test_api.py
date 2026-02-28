"""
Tests for the PreMortem Reddit Signal Engine API.
Run with:
    pytest test_api.py -v
    pytest test_api.py -v --tb=short   (shorter tracebacks)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from main import app
from models import StartupInput, SignalThread, Scores, AnalysisResponse, StatusUpdate
from mock_data import (
    SAMPLE_INPUTS,
    MOCK_ENGINE_RESULT,
    MOCK_THREADS,
    MOCK_SCORES,
    MOCK_COVERAGE,
    MOCK_REPORT,
    MOCK_GENERATED_QUERIES,
    MOCK_RAW_REDDIT_THREADS,
)


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────
@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─────────────────────────────────────────────────────────
# Pydantic Model Tests
# ─────────────────────────────────────────────────────────
class TestModels:
    """Test Pydantic models for validation."""

    def test_startup_input_valid(self):
        inp = StartupInput(
            idea="AI resume screener",
            problem="Manual screening takes too long",
            solution="Automated AI-based filtering",
            product_specs="Web app, $49/month",
        )
        assert inp.idea == "AI resume screener"
        assert inp.product_specs == "Web app, $49/month"

    def test_startup_input_min_length(self):
        with pytest.raises(Exception):
            StartupInput(idea="Hi", problem="Ok", solution="Yep")

    def test_startup_input_optional_specs(self):
        inp = StartupInput(
            idea="AI resume screener",
            problem="Manual screening takes too long",
            solution="Automated AI-based filtering",
        )
        assert inp.product_specs == ""

    def test_signal_thread_defaults(self):
        t = SignalThread()
        assert t.thread_id == ""
        assert t.relevance_score == 0
        assert t.competing_products == []
        assert t.signal_type == ""

    def test_signal_thread_from_mock(self):
        mock = MOCK_THREADS[0]
        t = SignalThread(**{k: v for k, v in mock.items() if k in SignalThread.model_fields})
        assert t.thread_id == "abc123"
        assert t.relevance_score == 95
        assert t.signal_type == "pain_point"
        assert "Lever" in t.competing_products

    def test_scores_defaults(self):
        s = Scores()
        assert s.demand_score == 0
        assert s.overall_failure_probability == 0

    def test_scores_from_mock(self):
        s = Scores(**MOCK_SCORES)
        assert s.demand_score == 78
        assert s.competition_risk == 65
        assert s.pain_validation == 88
        assert s.overall_failure_probability == 35

    def test_analysis_response_defaults(self):
        r = AnalysisResponse()
        assert r.report == ""
        assert r.threads == []
        assert r.iterations == 0

    def test_status_update(self):
        s = StatusUpdate(stage="searching", detail="Searching Reddit...")
        assert s.stage == "searching"


# ─────────────────────────────────────────────────────────
# Health & Root Endpoint Tests
# ─────────────────────────────────────────────────────────
class TestHealthEndpoints:

    @pytest.mark.anyio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "PreMortem" in data["engine"]

    @pytest.mark.anyio
    async def test_root(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "endpoints" in data
        assert "mock_full" in data["endpoints"]


# ─────────────────────────────────────────────────────────
# Mock Endpoint Tests
# ─────────────────────────────────────────────────────────
class TestMockEndpoints:

    @pytest.mark.anyio
    async def test_mock_analyze_returns_full_response(self, client):
        resp = await client.get("/mock/analyze")
        assert resp.status_code == 200
        data = resp.json()

        # Check top-level structure
        assert "report" in data
        assert "scores" in data
        assert "threads" in data
        assert "iterations" in data
        assert "queries_used" in data
        assert "coverage" in data
        assert "elapsed_seconds" in data

        # Validate scores
        scores = data["scores"]
        assert 0 <= scores["demand_score"] <= 100
        assert 0 <= scores["competition_risk"] <= 100
        assert 0 <= scores["pain_validation"] <= 100
        assert 0 <= scores["overall_failure_probability"] <= 100

        # Validate threads
        assert len(data["threads"]) == len(MOCK_THREADS)
        for thread in data["threads"]:
            assert "thread_id" in thread
            assert "relevance_score" in thread
            assert "signal_type" in thread

        # Check iterations
        assert data["iterations"] >= 1

    @pytest.mark.anyio
    async def test_mock_analyze_matches_response_model(self, client):
        resp = await client.get("/mock/analyze")
        data = resp.json()
        # Should be parseable as AnalysisResponse
        analysis = AnalysisResponse(**data)
        assert analysis.iterations == 2
        assert analysis.elapsed_seconds == 42.3

    @pytest.mark.anyio
    async def test_mock_report(self, client):
        resp = await client.get("/mock/report")
        assert resp.status_code == 200
        data = resp.json()
        assert "report" in data
        assert "Executive Summary" in data["report"]
        assert "Demand Signals" in data["report"]
        assert "Competition Landscape" in data["report"]
        assert "Recommendation" in data["report"]

    @pytest.mark.anyio
    async def test_mock_threads(self, client):
        resp = await client.get("/mock/threads")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == len(MOCK_THREADS)
        assert len(data["threads"]) == data["count"]

        # Check signal type distribution
        signal_types = [t["signal_type"] for t in data["threads"]]
        assert "pain_point" in signal_types
        assert "demand" in signal_types
        assert "competition" in signal_types
        assert "skepticism" in signal_types

    @pytest.mark.anyio
    async def test_mock_threads_have_required_fields(self, client):
        resp = await client.get("/mock/threads")
        data = resp.json()
        for thread in data["threads"]:
            assert thread["thread_id"], "thread_id should not be empty"
            assert thread["title"], "title should not be empty"
            assert thread["url"].startswith("https://"), "url should be valid"
            assert thread["subreddit"].startswith("r/"), "subreddit should start with r/"
            assert 0 <= thread["relevance_score"] <= 100
            assert thread["signal_type"] in ("pain_point", "competition", "demand", "skepticism", "irrelevant")

    @pytest.mark.anyio
    async def test_mock_scores(self, client):
        resp = await client.get("/mock/scores")
        assert resp.status_code == 200
        data = resp.json()
        assert data["demand_score"] == 78
        assert data["competition_risk"] == 65
        assert data["pain_validation"] == 88
        assert data["overall_failure_probability"] == 35

    @pytest.mark.anyio
    async def test_mock_queries(self, client):
        resp = await client.get("/mock/queries")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == len(MOCK_GENERATED_QUERIES)

        for q in data["queries"]:
            assert "query" in q
            assert "intent" in q
            assert "subreddits" in q
            assert q["intent"] in ("pain_point", "competition", "demand", "skepticism")
            assert len(q["subreddits"]) >= 1

    @pytest.mark.anyio
    async def test_mock_reddit_raw(self, client):
        resp = await client.get("/mock/reddit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == len(MOCK_RAW_REDDIT_THREADS)

        for thread in data["threads"]:
            assert "id" in thread
            assert "title" in thread
            assert "selftext" in thread
            assert "score" in thread
            assert "top_comments" in thread
            assert isinstance(thread["top_comments"], list)

    @pytest.mark.anyio
    async def test_mock_inputs(self, client):
        resp = await client.get("/mock/inputs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == len(SAMPLE_INPUTS)

        for inp in data["inputs"]:
            # Each input should be valid for StartupInput
            parsed = StartupInput(**inp)
            assert len(parsed.idea) >= 5
            assert len(parsed.problem) >= 5
            assert len(parsed.solution) >= 5


# ─────────────────────────────────────────────────────────
# POST /analyze Tests (with mocked engine)
# ─────────────────────────────────────────────────────────
class TestAnalyzeEndpoint:

    @pytest.mark.anyio
    async def test_analyze_with_mocked_engine(self, client):
        """POST /analyze with mocked engine should return valid response."""
        with patch("main.run_reddit_signal_engine", new_callable=AsyncMock) as mock_engine:
            mock_engine.return_value = MOCK_ENGINE_RESULT

            resp = await client.post("/analyze", json=SAMPLE_INPUTS[0])
            assert resp.status_code == 200
            data = resp.json()

            assert data["report"] != ""
            assert data["scores"]["demand_score"] == 78
            assert len(data["threads"]) > 0
            assert data["iterations"] == 2

    @pytest.mark.anyio
    async def test_analyze_invalid_input_short_idea(self, client):
        """POST /analyze with too-short fields should return 422."""
        resp = await client.post("/analyze", json={
            "idea": "Hi",
            "problem": "Ok",
            "solution": "Yep",
        })
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_analyze_missing_required_fields(self, client):
        """POST /analyze with missing fields should return 422."""
        resp = await client.post("/analyze", json={"idea": "Just an idea"})
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_analyze_empty_body(self, client):
        """POST /analyze with empty body should return 422."""
        resp = await client.post("/analyze", json={})
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_analyze_engine_error_returns_500(self, client):
        """POST /analyze should return 500 if the engine raises."""
        with patch("main.run_reddit_signal_engine", new_callable=AsyncMock) as mock_engine:
            mock_engine.side_effect = RuntimeError("OpenAI API error")

            resp = await client.post("/analyze", json=SAMPLE_INPUTS[0])
            assert resp.status_code == 500
            assert "OpenAI API error" in resp.json()["detail"]


# ─────────────────────────────────────────────────────────
# POST /analyze/stream Tests
# ─────────────────────────────────────────────────────────
class TestStreamEndpoint:

    @pytest.mark.anyio
    async def test_stream_with_mocked_engine(self, client):
        """POST /analyze/stream should return SSE events."""
        with patch("main.run_reddit_signal_engine", new_callable=AsyncMock) as mock_engine:
            mock_engine.return_value = MOCK_ENGINE_RESULT

            resp = await client.post("/analyze/stream", json=SAMPLE_INPUTS[0])
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")

            # The response body should contain SSE data lines
            body = resp.text
            assert "data:" in body


# ─────────────────────────────────────────────────────────
# Mock Data Integrity Tests
# ─────────────────────────────────────────────────────────
class TestMockDataIntegrity:
    """Validate that mock data is internally consistent."""

    def test_all_sample_inputs_are_valid(self):
        for inp in SAMPLE_INPUTS:
            parsed = StartupInput(**inp)
            assert parsed.idea
            assert parsed.problem
            assert parsed.solution

    def test_all_mock_threads_have_valid_signal_types(self):
        valid_types = {"pain_point", "competition", "demand", "skepticism", "irrelevant"}
        for t in MOCK_THREADS:
            assert t["signal_type"] in valid_types, f"Invalid signal_type: {t['signal_type']}"

    def test_all_mock_threads_have_relevance_in_range(self):
        for t in MOCK_THREADS:
            assert 0 <= t["relevance_score"] <= 100, f"Score out of range: {t['relevance_score']}"

    def test_mock_scores_in_range(self):
        for key, val in MOCK_SCORES.items():
            assert 0 <= val <= 100, f"{key} out of range: {val}"

    def test_mock_coverage_counts_match_threads(self):
        counts = MOCK_COVERAGE["counts"]
        actual_counts = {}
        for t in MOCK_THREADS:
            st = t["signal_type"]
            actual_counts[st] = actual_counts.get(st, 0) + 1
        for signal_type, count in counts.items():
            assert count == actual_counts.get(signal_type, 0), \
                f"Coverage mismatch for {signal_type}: expected {actual_counts.get(signal_type, 0)}, got {count}"

    def test_mock_queries_cover_all_intents(self):
        intents = {q["intent"] for q in MOCK_GENERATED_QUERIES}
        assert "pain_point" in intents
        assert "demand" in intents
        assert "competition" in intents
        assert "skepticism" in intents

    def test_mock_engine_result_has_all_keys(self):
        required_keys = {"report", "scores", "threads", "iterations", "queries_used", "coverage", "elapsed_seconds"}
        assert required_keys.issubset(MOCK_ENGINE_RESULT.keys())

    def test_mock_report_has_all_sections(self):
        required_sections = [
            "Executive Summary",
            "Demand Signals",
            "Competition Landscape",
            "Pain Points Validated",
            "Red Flags",
            "Unmet Needs",
            "Recommendation",
        ]
        for section in required_sections:
            assert section in MOCK_REPORT, f"Missing report section: {section}"
