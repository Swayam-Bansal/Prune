import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

// ── Complex tech keywords that raise execution risk ──────────────────────────
const COMPLEX_TECH = [
  "ai",
  "artificial intelligence",
  "machine learning",
  "deep learning",
  "neural network",
  "llm",
  "gpt",
  "hardware",
  "iot",
  "internet of things",
  "blockchain",
  "crypto",
  "decentralized",
  "robotics",
  "drone",
  "satellite",
  "biotech",
  "genomics",
  "quantum",
  "infra",
  "infrastructure",
  "embedded",
];

function executionComplexity(ideaText) {
  const lower = ideaText.toLowerCase();
  let score = 36;
  for (const kw of COMPLEX_TECH) {
    if (lower.includes(kw)) score += 8;
  }
  return Math.min(score, 92);
}

// ── Main handler ─────────────────────────────────────────────────────────────

export async function POST(req) {
  try {
    const { idea } = await req.json();

    if (!idea || idea.trim().length < 10) {
      return NextResponse.json(
        { error: "Please provide a startup idea (at least 10 characters)." },
        { status: 400 },
      );
    }

    // ── Step 1: OpenAI — keyword extraction + problem/solution extraction ────
    const oaiRes = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          {
            role: "system",
            content:
              "You are a startup idea analyst. Return ONLY valid JSON with no markdown, no explanation.",
          },
          {
            role: "user",
            content: `Analyze this startup idea: "${idea.trim()}"\n\nReturn exactly this JSON shape:\n{"main_problem": "short phrase describing the problem", "target_market": "short phrase", "core_keywords": ["keyword1", "keyword2", "keyword3"], "solution": "one sentence describing the solution", "product_specs": "brief technical approach"}`,
          },
        ],
        temperature: 0,
        max_tokens: 300,
      }),
    });

    if (!oaiRes.ok) {
      const e = await oaiRes.json().catch(() => ({}));
      throw new Error(`OpenAI error: ${e.error?.message || oaiRes.statusText}`);
    }

    const oaiJson = await oaiRes.json();
    let extracted;
    try {
      const raw = oaiJson.choices[0].message.content.trim();
      extracted = JSON.parse(raw);
    } catch {
      throw new Error(
        "Could not parse keyword extraction. Check your OPENAI_API_KEY.",
      );
    }

    const {
      core_keywords = [],
      main_problem = "",
      target_market = "",
      solution = "",
      product_specs = "",
    } = extracted;

    // ── Step 2: Call FastAPI backend /analyze with full startup input ─────────
    const backendRes = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        idea: idea.trim(),
        problem: main_problem,
        solution: solution,
        product_specs: product_specs,
      }),
    });

    if (!backendRes.ok) {
      const errBody = await backendRes.text().catch(() => "");
      console.error(
        "[/api/analyze] Backend error:",
        backendRes.status,
        errBody,
      );
      throw new Error(`Backend analysis failed (${backendRes.status})`);
    }

    const backend = await backendRes.json();

    // ── Step 3: Map backend response to frontend shape ───────────────────────
    const githubData = backend.github || {};
    const websearchData = backend.websearch || {};
    const redditData = backend.reddit || {};
    const scores = backend.scores || {};
    const breakdown = scores.breakdown || {};

    const githubCount = githubData.total_count || 0;
    const githubFilteredCount = githubData.filtered_count || 0;
    const numCompanies = websearchData.num_companies_found || 0;
    const redditThreads = redditData.threads || [];

    const compRisk = Math.round(scores.competition_risk ?? 50);
    const demStr = Math.min(85, Math.max(20, 20 + numCompanies * 10));
    const execRisk = executionComplexity(idea);
    const satRisk = Math.round(
      (breakdown.websearch_competition ?? 0) * 0.6 +
        (breakdown.github_competition ?? 0) * 0.4,
    );
    const failProb = Math.min(
      100,
      Math.round(
        compRisk * 0.4 +
          execRisk * 0.25 +
          satRisk * 0.2 +
          (100 - demStr) * 0.15,
      ),
    );

    // Build similar startups from websearch companies + deep_dives
    const companies = websearchData.companies || [];
    const deepDives = websearchData.deep_dives || [];

    const similar_startups = companies.map((c) => {
      const dive = deepDives.find(
        (d) => d?.company?.name === c.name || d?.company?.domain === c.domain,
      );
      return {
        name: c.name || c.domain || "Unknown",
        desc:
          c.one_liner ||
          dive?.profile?.what_they_do ||
          (typeof dive?.profile === "string" ? dive.profile : "") ||
          "",
        url: c.domain ? `https://${c.domain}` : c.homepage || "#",
        stage: c.domain || "startup",
        similarity: Math.round((c.similarity_score ?? 0) * 100),
      };
    });

    // Build reddit thread cards
    const reddit_threads = redditThreads.slice(0, 8).map((t) => {
      // relevance_score is 0-10 integer from the Reddit engine
      const relScore = t.relevance_score || 0;
      const similarity =
        relScore > 1
          ? Math.min(relScore * 10, 100)
          : Math.round(relScore * 100);
      const painPoints =
        t.unmet_needs && t.unmet_needs.length > 0
          ? t.unmet_needs
          : t.key_quotes && t.key_quotes.length > 0
            ? t.key_quotes
            : [t.insight || "Signal detected"];
      return {
        title: t.title || t.insight || "",
        url: t.url || "#",
        subreddit: t.subreddit || "reddit",
        upvotes: t.score || 0,
        comments: t.num_comments || 0,
        similarity,
        pain_points: painPoints,
        competition_signal:
          t.signal_type === "competition" ? "High" : "Moderate",
      };
    });

    // Build top repos
    const top_repos = (githubData.repositories || []).map((r) => ({
      name: r.name || "",
      description: r.description || "",
      stars: r.stars || 0,
      language: r.language || "",
      url: r.url || "#",
    }));

    // Build insights
    const insights = [];
    if (githubCount >= 500) {
      insights.push(
        `${githubCount.toLocaleString()} GitHub repos exist in this space — a heavily competed OSS ecosystem; differentiation must be sharp.`,
      );
    } else if (githubCount >= 50) {
      insights.push(
        `${githubCount} GitHub repositories found — active developer space. A clear unique value proposition is essential.`,
      );
    } else {
      insights.push(
        `Only ${githubCount} GitHub repos found — sparse developer competition signals a potential early-mover advantage.`,
      );
    }

    if (numCompanies >= 5) {
      insights.push(
        `${numCompanies} similar companies identified via web search — this is a validated market with established players. Find your niche.`,
      );
    } else if (numCompanies >= 2) {
      insights.push(
        `${numCompanies} competing companies found — some market validation exists, but there's room for a differentiated entrant.`,
      );
    } else {
      insights.push(
        `Few direct competitors found via web search — either a novel space or search terms need broadening.`,
      );
    }

    if (redditThreads.length >= 10) {
      insights.push(
        `${redditThreads.length} relevant Reddit threads found — strong community discussion validates real user pain and demand.`,
      );
    } else if (redditThreads.length >= 3) {
      insights.push(
        `${redditThreads.length} Reddit discussions found — moderate demand signal; users are talking about this problem.`,
      );
    } else {
      insights.push(
        `Few Reddit signals found — the problem may not yet be widely articulated online, or niche search terms are needed.`,
      );
    }

    if (redditData.report) {
      const reportStr =
        typeof redditData.report === "string"
          ? redditData.report
          : JSON.stringify(redditData.report);
      insights.push(
        reportStr.slice(0, 300) + (reportStr.length > 300 ? "..." : ""),
      );
    }

    if (execRisk >= 72) {
      insights.push(
        `Complex technical domain detected — high execution risk; plan for longer build cycles and specialized hiring.`,
      );
    } else if (execRisk >= 50) {
      insights.push(
        `Moderate technical complexity — achievable with a capable small team, but scope creep is a real risk.`,
      );
    } else {
      insights.push(
        `Low execution complexity — standard engineering stack; a lean team can ship a viable MVP quickly.`,
      );
    }

    return NextResponse.json({
      // Raw signals
      github_repo_count: githubFilteredCount,
      web_result_count: numCompanies,
      reddit_signal_count: redditThreads.length,

      // Derived scores (0–100)
      competition_risk: compRisk,
      demand_strength: demStr,
      market_saturation_risk: satRisk,
      execution_complexity_risk: execRisk,
      final_failure_probability: failProb,

      // Score breakdown
      score_breakdown: breakdown,
      weights: backend.weights || {},

      // Narrative
      insights,

      // Metadata
      keywords: { main_problem, target_market, core_keywords },

      // Rich data
      top_repos,
      similar_startups,
      reddit_threads,
    });
  } catch (err) {
    console.error("[/api/analyze]", err);
    return NextResponse.json(
      { error: err.message || "Analysis failed. Check server logs." },
      { status: 500 },
    );
  }
}
