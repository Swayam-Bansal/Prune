import { NextResponse } from 'next/server';

// ── Complex tech keywords that raise execution risk ──────────────────────────
const COMPLEX_TECH = [
  'ai', 'artificial intelligence', 'machine learning', 'deep learning',
  'neural network', 'llm', 'gpt', 'hardware', 'iot', 'internet of things',
  'blockchain', 'crypto', 'decentralized', 'robotics', 'drone', 'satellite',
  'biotech', 'genomics', 'quantum', 'infra', 'infrastructure', 'embedded',
];

// ── Deterministic scoring functions ─────────────────────────────────────────

function competitionRisk(githubCount) {
  if (githubCount >= 2000) return 92;
  if (githubCount >= 500)  return 78;
  if (githubCount >= 100)  return 62;
  if (githubCount >= 25)   return 44;
  if (githubCount >= 5)    return 26;
  return 12;
}

function demandStrength(redditMatches) {
  if (redditMatches >= 500_000)  return 90;
  if (redditMatches >= 100_000)  return 74;
  if (redditMatches >= 10_000)   return 56;
  if (redditMatches >= 1_000)    return 38;
  if (redditMatches >= 100)      return 22;
  return 10;
}

function saturationRisk(webMatches) {
  if (webMatches >= 50_000_000)  return 88;
  if (webMatches >= 10_000_000)  return 74;
  if (webMatches >= 1_000_000)   return 58;
  if (webMatches >= 100_000)     return 40;
  if (webMatches >= 10_000)      return 24;
  return 12;
}

function executionComplexity(ideaText) {
  const lower = ideaText.toLowerCase();
  let score = 36;
  for (const kw of COMPLEX_TECH) {
    if (lower.includes(kw)) score += 8;
  }
  return Math.min(score, 92);
}

function failureProbability(comp, demand, sat, exec) {
  // High competition + low demand = bad. Deterministic formula.
  const raw = comp * 0.30 + sat * 0.25 + (100 - demand) * 0.30 + exec * 0.15;
  return Math.min(Math.round(raw), 99);
}

function buildInsights({ githubCount, webCount, redditCount, execScore, keywords }) {
  const insights = [];

  // Competition
  if (githubCount >= 500) {
    insights.push(`${githubCount.toLocaleString()} GitHub repos exist in this space — a heavily competed OSS ecosystem; differentiation must be sharp.`);
  } else if (githubCount >= 50) {
    insights.push(`${githubCount} GitHub repositories found — active developer space. A clear unique value proposition is essential.`);
  } else {
    insights.push(`Only ${githubCount} GitHub repos found — sparse developer competition signals a potential early-mover advantage.`);
  }

  // Market saturation
  if (webCount >= 10_000_000) {
    insights.push(`${(webCount / 1_000_000).toFixed(0)}M+ web results — crowded market with established players. SEO and paid acquisition will be expensive.`);
  } else if (webCount >= 100_000) {
    insights.push(`${(webCount / 1_000).toFixed(0)}K web market results — meaningful existing presence; positioning and niche targeting are critical.`);
  } else {
    insights.push(`Low web saturation (${webCount.toLocaleString()} results) — emerging or niche market with potential whitespace to capture.`);
  }

  // Demand
  if (redditCount >= 100_000) {
    insights.push(`Strong Reddit demand signal (${(redditCount / 1_000).toFixed(0)}K+ discussions) — real user pain vocalized online validates strong market need.`);
  } else if (redditCount >= 5_000) {
    insights.push(`Moderate Reddit activity (${(redditCount / 1_000).toFixed(0)}K discussions) — demand exists but may not be acute or time-sensitive.`);
  } else {
    insights.push(`Low Reddit signal (${redditCount.toLocaleString()} results) — nascent problem or one users haven't articulated online at scale.`);
  }

  // Execution
  if (execScore >= 72) {
    insights.push(`Complex technical domain detected (${keywords.slice(0, 2).join(', ')}) — high execution risk; plan for longer build cycles and specialized hiring.`);
  } else if (execScore >= 50) {
    insights.push(`Moderate technical complexity — achievable with a capable small team, but scope creep in early sprints is a real risk.`);
  } else {
    insights.push(`Low execution complexity — standard engineering stack; a lean team can ship a viable MVP within typical startup timelines.`);
  }

  return insights;
}

// ── Fetch helpers with error isolation ──────────────────────────────────────

async function fetchGitHub(query) {
  try {
    const url = `https://api.github.com/search/repositories?q=${encodeURIComponent(query)}&per_page=5&sort=stars`;
    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
    });
    if (!res.ok) return { total_count: 0, items: [] };
    const json = await res.json();
    return {
      total_count: json.total_count ?? 0,
      items: (json.items || []).map(r => ({
        name: r.full_name,
        stars: r.stargazers_count,
        url: r.html_url,
      })),
    };
  } catch {
    return { total_count: 0, items: [] };
  }
}

async function fetchBing(query) {
  try {
    const url = `https://api.bing.microsoft.com/v7.0/search?q=${encodeURIComponent(query)}&count=5&mkt=en-US&responseFilter=Webpages`;
    const res = await fetch(url, {
      headers: { 'Ocp-Apim-Subscription-Key': process.env.BING_API_KEY },
    });
    if (!res.ok) return { totalEstimatedMatches: 0, value: [] };
    const json = await res.json();
    return {
      totalEstimatedMatches: json.webPages?.totalEstimatedMatches ?? 0,
      value: (json.webPages?.value || []).map(v => v.name),
    };
  } catch {
    return { totalEstimatedMatches: 0, value: [] };
  }
}

// ── Main handler ─────────────────────────────────────────────────────────────

export async function POST(req) {
  try {
    const { idea } = await req.json();

    if (!idea || idea.trim().length < 10) {
      return NextResponse.json(
        { error: 'Please provide a startup idea (at least 10 characters).' },
        { status: 400 }
      );
    }

    // ── Step 1: OpenAI — keyword extraction only ─────────────────────────────
    const oaiRes = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'system',
            content:
              'You are a keyword extractor for startup ideas. Return ONLY valid JSON with no markdown, no explanation.',
          },
          {
            role: 'user',
            content: `Extract from this startup idea: "${idea.trim()}"\n\nReturn exactly this JSON shape:\n{"main_problem": "short phrase", "target_market": "short phrase", "core_keywords": ["keyword1", "keyword2", "keyword3"]}`,
          },
        ],
        temperature: 0,
        max_tokens: 180,
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
      throw new Error('Could not parse keyword extraction. Check your OPENAI_API_KEY.');
    }

    const { core_keywords = [], main_problem = '', target_market = '' } = extracted;
    const kwQuery = core_keywords.join(' ');

    // ── Step 2: Parallel external signal collection ──────────────────────────
    const [gh, bingWeb, bingReddit] = await Promise.all([
      // A. GitHub — measures developer competition
      fetchGitHub(kwQuery),

      // B. Bing Web — measures market saturation
      fetchBing(`${kwQuery} startup OR SaaS OR tool OR software`),

      // C. Bing Reddit — measures real user demand / pain
      fetchBing(`${main_problem} site:reddit.com`),
    ]);

    const githubCount  = gh.total_count;
    const webCount     = bingWeb.totalEstimatedMatches;
    const redditCount  = bingReddit.totalEstimatedMatches;

    // ── Step 3: Deterministic scoring — no AI involved ───────────────────────
    const compRisk  = competitionRisk(githubCount);
    const demStr    = demandStrength(redditCount);
    const satRisk   = saturationRisk(webCount);
    const execRisk  = executionComplexity(idea);
    const failProb  = failureProbability(compRisk, demStr, satRisk, execRisk);

    return NextResponse.json({
      // Raw signals
      github_repo_count:    githubCount,
      web_result_count:     webCount,
      reddit_signal_count:  redditCount,

      // Derived scores (0–100)
      competition_risk:          compRisk,
      demand_strength:           demStr,
      market_saturation_risk:    satRisk,
      execution_complexity_risk: execRisk,
      final_failure_probability: failProb,

      // Narrative
      insights: buildInsights({
        githubCount,
        webCount,
        redditCount,
        execScore: execRisk,
        keywords: core_keywords,
      }),

      // Metadata
      keywords: { main_problem, target_market, core_keywords },
      top_repos:  gh.items,
      top_web:    bingWeb.value,
      top_reddit: bingReddit.value,
    });
  } catch (err) {
    console.error('[/api/analyze]', err);
    return NextResponse.json(
      { error: err.message || 'Analysis failed. Check server logs.' },
      { status: 500 }
    );
  }
}
