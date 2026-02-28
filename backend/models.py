"""
Pydantic models for API request / response.
"""
from pydantic import BaseModel, Field
from typing import Optional


class StartupInput(BaseModel):
    """What the founder provides."""
    idea: str = Field(..., description="One-line startup idea", min_length=5)
    problem: str = Field(default="", description="The problem being solved")
    solution: str = Field(default="", description="How the product solves it")
    product_specs: str = Field(
        default="",
        description="Technical details, features, target platform, etc.",
    )
    deep_mode: bool = Field(
        default=False,
        description="If True, includes Reddit analysis (slower, 2-3 mins)",
    )


class SignalThread(BaseModel):
    """A single analyzed Reddit thread."""
    thread_id: str = ""
    title: str = ""
    url: str = ""
    subreddit: str = ""
    score: int = 0
    num_comments: int = 0
    relevance_score: int = 0
    signal_type: str = ""
    insight: str = ""
    competing_products: list[str] = []
    unmet_needs: list[str] = []
    key_quotes: list[str] = []
    source_query: str = ""


class Scores(BaseModel):
    """Risk scores."""
    demand_score: int = 0
    competition_risk: int = 0
    pain_validation: int = 0
    overall_failure_probability: int = 0


class AnalysisResponse(BaseModel):
    """Full response from the engine."""
    report: str = ""
    scores: Scores = Scores()
    threads: list[SignalThread] = []
    iterations: int = 0
    queries_used: list[str] = []
    coverage: dict = {}
    elapsed_seconds: float = 0.0


class StatusUpdate(BaseModel):
    """Server-Sent Event payload."""
    stage: str
    detail: str
