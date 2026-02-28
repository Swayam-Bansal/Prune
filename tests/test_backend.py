import json
import os

import pytest
from fastapi.testclient import TestClient

from backend.main import (
    app,
    extract_keywords,
    compute_competition_risk,
    compute_relevance,
    compute_top_matches,
    build_github_query,
)


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_compute_risk():
    assert compute_competition_risk(0) == 0.0
    assert compute_competition_risk(50) == 0.5
    assert compute_competition_risk(100) == 1.0
    assert compute_competition_risk(150) == 1.0


def test_compute_relevance():
    repos = [
        {"name": "dog-social", "description": "A network for dog owners"},
        {"name": "cat-app", "description": "social app for cats"},
    ]
    kw = ["dog", "network"]
    score = compute_relevance(kw, repos)
    # first repo matches two keywords, second repo matches none
    assert score == pytest.approx(0.5)


def test_extract_keywords_fallback():
    # with no GEMINI_API_KEY the function should still return first 5 words
    kw = extract_keywords("this is a very simple idea example for test")
    assert isinstance(kw, list)
    assert len(kw) <= 5


@pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"), reason="requires GITHUB_TOKEN env"
)
def test_github_search_live():
    # This hits GitHub – use a generic query that should return something.
    response = client.post("/github/search", json={"idea": "todo list"})
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert isinstance(data["total_count"], int)


def test_compute_top_matches():
    idea = "An AI copilot that turns meeting transcripts into Jira tickets"
    keywords = ["copilot", "meeting", "transcript", "jira"]
    repos = [
        {"name": "foo/meeting-copilot", "description": "AI meeting copilot for transcripts", "stars": 5},
        {"name": "foo/jira-bot", "description": "Automatically creates Jira tickets from notes", "stars": 3},
        {"name": "foo/bee-movie", "description": "According to all known laws of aviation", "stars": 200},
        {"name": "foo/transcript-tool", "description": "Parses meeting transcripts into action items", "stars": 1},
        {"name": "foo/unrelated", "description": "A recipe app for cooking enthusiasts", "stars": 0},
    ]
    matches = compute_top_matches(idea, keywords, repos)
    names = [r["name"] for r in matches]
    # bee-movie and recipe app should be excluded or ranked last
    assert "foo/meeting-copilot" in names
    assert "foo/jira-bot" in names
    assert "foo/transcript-tool" in names
    assert "foo/bee-movie" not in names
    assert "foo/unrelated" not in names
    # all results must carry a match_score
    assert all("match_score" in r for r in matches)
    # results must be sorted descending by score
    scores = [r["match_score"] for r in matches]
    assert scores == sorted(scores, reverse=True)


def test_top_matches_excludes_bee_movie_repos():
    """Bee Movie repos must never appear in top_matches for the Jira idea."""
    idea = "An AI copilot that automatically turns meeting transcripts into Jira tickets and follow-up tasks for small teams"
    keywords = ["copilot", "meeting", "transcript", "jira", "tasks"]
    bee_movie_desc = (
        "According to all known laws of aviation, there is no way that a bee "
        "should be able to fly. Its wings are too small to get its fat little body off the ground."
    )
    repos = [
        {"name": "danderfer/Comp_Sci_Sem_2", "description": bee_movie_desc, "stars": 173},
        {"name": "MarkipTheMudkip/in-class-project-2", "description": bee_movie_desc, "stars": 76},
        {"name": "S4ltster/Beemovie", "description": bee_movie_desc, "stars": 40},
        {"name": "foo/meeting-copilot", "description": "AI meeting copilot for transcripts and tasks", "stars": 5},
        {"name": "foo/jira-transcript-bot", "description": "Converts meeting transcripts into Jira tickets", "stars": 2},
    ]
    matches = compute_top_matches(idea, keywords, repos)
    names = [r["name"] for r in matches]
    assert "danderfer/Comp_Sci_Sem_2" not in names
    assert "MarkipTheMudkip/in-class-project-2" not in names
    assert "S4ltster/Beemovie" not in names
    assert "foo/meeting-copilot" in names
    assert "foo/jira-transcript-bot" in names


def test_build_github_query_prefers_specific_terms():
    """Tier-1 specific terms (jira, transcript) should beat tier-2 generic ones (meeting, copilot)."""
    # When Gemini extracts domain-specific terms, they should lead the query
    kw_specific = ["jira", "transcript", "copilot", "meeting"]
    query = build_github_query(kw_specific)
    # jira and transcript are tier-1; they must appear in the query
    assert "jira" in query
    assert "transcript" in query
    assert "in:name,description" in query

    # When only tier-2 words are available, use them
    kw_generic = ["meeting", "copilot", "assistant"]
    query2 = build_github_query(kw_generic)
    assert "in:name,description" in query2
    assert len(query2) > len("in:name,description")


def test_analyze_with_mock(monkeypatch):
    # simulate extraction and github search so test doesn't depend on network
    monkeypatch.setenv("GITHUB_TOKEN", "fake")

    def fake_extract(text):
        return ["foo", "bar"]

    def fake_search(q):
        return {"total_count": 2, "items": [
            {"name": "foo-project", "description": "contains foo"},
            {"name": "unrelated", "description": "no match"},
        ]}

    monkeypatch.setattr("backend.main.extract_keywords", fake_extract)
    monkeypatch.setattr("backend.main.search_github", fake_search)

    res = client.post("/analyze", json={"idea": "doesn' matter"})
    assert res.status_code == 200
    out = res.json()
    assert out["keywords"] == ["foo", "bar"]
    gh = out["github"]
    assert gh["total_count"] == 2
    assert gh["competition_risk"] == pytest.approx(0.02)
    assert gh["relevance_score"] == pytest.approx(0.5)
    assert isinstance(gh["repositories"], list)
