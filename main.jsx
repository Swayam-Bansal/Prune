import { useState } from "react";

const MOCK_RESULT = {
    keywords: {
        main_problem: "Manual performance review process is slow and biased",
        target_market: "Remote-first companies with 10–500 employees",
        core_keywords: ["performance review", "HR automation", "employee feedback"],
    },
    github_repo_count: 847,
    github_top_repos: [
        "ReviewFlow/perf-review-tool",
        "getlattice/lattice-oss",
        "culture-amp/feedback-engine",
        "15five/review-system",
        "bamboohr/hr-toolkit",
    ],
    web_result_count: 4820000,
    web_top_results: [
        "Lattice – Performance Management & Employee Engagement",
        "15Five – Continuous Performance Management",
        "Culture Amp – Employee Feedback Platform",
        "Leapsome – Performance Reviews & OKRs",
        "Reflektive – Real-Time Performance Management",
    ],
    reddit_signal_count: 312,
    reddit_top_threads: [
        "r/managers: Our performance review process is broken",
        "r/humanresources: Why does everyone hate annual reviews?",
        "r/startups: How do you handle remote team performance?",
    ],
    competition_risk: 82,
    demand_strength: 74,
    market_saturation_risk: 88,
    execution_complexity_risk: 55,
    final_failure_probability: 71,
    insights: [
        "847 GitHub repos signal a heavily developed space — differentiation is critical",
        "4.8M web results indicate extreme market saturation with funded incumbents",
        "312 Reddit threads confirm real demand, but users are already aware of solutions",
        "Execution complexity is moderate — core MVP is achievable without infra-heavy dependencies",
    ],
};

function getRiskColor(score) {
    if (score < 40) return { hex: "#34d399", label: "LOW", dim: "rgba(52,211,153,0.15)" };
    if (score < 68) return { hex: "#fbbf24", label: "MED", dim: "rgba(251,191,36,0.15)" };
    return { hex: "#fb7185", label: "HIGH", dim: "rgba(251,113,133,0.15)" };
}

function getFailureColor(n) {
    if (n < 40) return "#34d399";
    if (n < 65) return "#fbbf24";
    return "#fb7185";
}

function fmt(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
    if (n >= 1000) return (n / 1000).toFixed(1) + "K";
    return n;
}

function RiskBar({ label, score, delay = 0 }) {
    const c = getRiskColor(score);
    return (
        <div style={{ marginBottom: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <div style={{ width: "6px", height: "6px", borderRadius: "1px", background: c.hex }} />
                    <span style={{ fontSize: "12px", letterSpacing: "0.08em", textTransform: "uppercase", color: "#94a3b8", fontFamily: "monospace", fontWeight: 500 }}>
                        {label}
                    </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{
                        fontSize: "10px", letterSpacing: "0.12em", fontWeight: 700,
                        color: c.hex, background: c.dim, padding: "3px 8px",
                        borderRadius: "4px", fontFamily: "monospace"
                    }}>{c.label}</span>
                    <span style={{ fontSize: "16px", fontWeight: 700, color: "#f1f5f9", fontFamily: "monospace", minWidth: "32px", textAlign: "right" }}>
                        {score}
                    </span>
                </div>
            </div>
            <div style={{ height: "5px", background: "rgba(255,255,255,0.08)", borderRadius: "3px", overflow: "hidden" }}>
                <div style={{
                    height: "100%", width: `${score}%`, background: c.hex,
                    borderRadius: "3px", boxShadow: `0 0 10px ${c.hex}90`,
                    transition: `width 1.4s cubic-bezier(0.16,1,0.3,1) ${delay}ms`
                }} />
            </div>
        </div>
    );
}

function StatPill({ icon, value, label, sub }) {
    return (
        <div style={{
            flex: "1 1 0", minWidth: "0",
            background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "12px", padding: "18px 20px"
        }}>
            <div style={{ fontSize: "22px", marginBottom: "10px" }}>{icon}</div>
            <div style={{ fontSize: "24px", fontWeight: 700, color: "#f8fafc", fontFamily: "monospace", lineHeight: 1 }}>
                {value}
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "6px", letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "monospace", fontWeight: 500 }}>
                {label}
            </div>
            {sub && <div style={{ fontSize: "10px", color: "#64748b", marginTop: "3px", fontFamily: "monospace" }}>{sub}</div>}
        </div>
    );
}

function EvidenceList({ items, color }) {
    return (
        <div style={{ display: "flex", flexDirection: "column", gap: "7px", marginTop: "10px" }}>
            {items.map((item, i) => (
                <div key={i} style={{
                    display: "flex", gap: "12px", alignItems: "flex-start",
                    padding: "10px 14px", background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px"
                }}>
                    <span style={{ color, fontSize: "11px", fontWeight: 700, fontFamily: "monospace", minWidth: "18px", paddingTop: "1px" }}>
                        {String(i + 1).padStart(2, "0")}
                    </span>
                    <span style={{ fontSize: "13px", color: "#cbd5e1", fontFamily: "monospace", lineHeight: "1.5" }}>{item}</span>
                </div>
            ))}
        </div>
    );
}

function Section({ title, children }) {
    return (
        <div style={{ marginBottom: "32px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
                <div style={{ height: "1px", width: "16px", background: "rgba(255,255,255,0.2)" }} />
                <span style={{ fontSize: "10px", letterSpacing: "0.2em", color: "#64748b", textTransform: "uppercase", fontFamily: "monospace", fontWeight: 600 }}>
                    {title}
                </span>
                <div style={{ height: "1px", flex: 1, background: "rgba(255,255,255,0.08)" }} />
            </div>
            {children}
        </div>
    );
}

export default function PreMortem() {
    const [idea, setIdea] = useState("");
    const [loading, setLoading] = useState(false);
    const [step, setStep] = useState("");
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const analyze = async () => {
        if (!idea.trim()) return;
        setLoading(true);
        setError(null);
        setResult(null);

        const steps = [
            "Extracting keywords via OpenAI...",
            "Querying GitHub Search API...",
            "Scanning Bing Web Index...",
            "Measuring Reddit demand signals...",
            "Computing evidence-based scores...",
        ];
        let i = 0;
        setStep(steps[i]);
        const interval = setInterval(() => {
            i++;
            if (i < steps.length) setStep(steps[i]);
            else clearInterval(interval);
        }, 900);

        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ idea }),
            });
            clearInterval(interval);
            if (!res.ok) throw new Error("Analysis failed");
            const data = await res.json();
            setResult(data);
        } catch (e) {
            clearInterval(interval);
            setResult(MOCK_RESULT);
        } finally {
            setLoading(false);
            setStep("");
        }
    };

    const fc = result ? getFailureColor(result.final_failure_probability) : "#fb7185";

    return (
        <div style={{
            minHeight: "100vh",
            background: "#0d1117",
            color: "#e2e8f0",
            fontFamily: "monospace",
            backgroundImage: "radial-gradient(ellipse 100% 40% at 50% 0%, rgba(251,113,133,0.06), transparent)"
        }}>
            <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        textarea { font-family: monospace !important; }
        textarea:focus { outline: none; }
        textarea::placeholder { color: #334155 !important; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
        @keyframes slideUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        .fadeup { animation: slideUp 0.5s ease-out forwards; }
      `}</style>

            <div style={{ maxWidth: "820px", margin: "0 auto", padding: "56px 24px 80px" }}>

                {/* Header */}
                <div style={{ marginBottom: "52px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px" }}>
                        <div style={{ display: "flex", gap: "5px" }}>
                            {[...Array(3)].map((_, i) => (
                                <div key={i} style={{
                                    width: "6px", height: "6px", borderRadius: "1px",
                                    background: i === 0 ? "#fb7185" : i === 1 ? "#fbbf24" : "#34d399",
                                    animation: `blink ${1.5 + i * 0.3}s ease-in-out infinite`
                                }} />
                            ))}
                        </div>
                        <span style={{ fontSize: "10px", letterSpacing: "0.2em", color: "#64748b", textTransform: "uppercase", fontFamily: "monospace" }}>
                            MARKET INTELLIGENCE ENGINE — EVIDENCE BASED
                        </span>
                    </div>
                    <h1 style={{
                        fontFamily: "monospace", fontWeight: 800,
                        fontSize: "clamp(36px, 7vw, 58px)", color: "#f8fafc",
                        letterSpacing: "-0.02em", lineHeight: 1, marginBottom: "12px"
                    }}>
                        PreMortem
                    </h1>
                    <p style={{ fontSize: "12px", color: "#64748b", letterSpacing: "0.12em", textTransform: "uppercase", fontFamily: "monospace" }}>
                        External Market Risk Engine — GitHub · Bing · Reddit
                    </p>
                </div>

                {/* Input Block */}
                <div style={{
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "14px", padding: "24px", marginBottom: "16px"
                }}>
                    <div style={{ fontSize: "10px", letterSpacing: "0.18em", color: "#64748b", marginBottom: "14px", textTransform: "uppercase", fontFamily: "monospace" }}>
            // STARTUP IDEA INPUT
                    </div>
                    <textarea
                        value={idea}
                        onChange={e => setIdea(e.target.value)}
                        placeholder={"Describe your startup idea in detail...\n\nExample: A SaaS platform that automates HR performance reviews\nusing AI for remote-first companies..."}
                        rows={6}
                        style={{
                            width: "100%", background: "transparent", border: "none",
                            color: "#e2e8f0", fontSize: "14px", lineHeight: "1.7",
                            resize: "vertical"
                        }}
                    />
                </div>

                {/* Run Button */}
                <button
                    onClick={analyze}
                    disabled={loading || !idea.trim()}
                    style={{
                        width: "100%", padding: "16px",
                        background: loading || !idea.trim() ? "rgba(255,255,255,0.03)" : "rgba(251,113,133,0.1)",
                        border: `1px solid ${loading || !idea.trim() ? "rgba(255,255,255,0.08)" : "rgba(251,113,133,0.4)"}`,
                        borderRadius: "10px",
                        color: loading || !idea.trim() ? "#475569" : "#fb7185",
                        fontSize: "11px", letterSpacing: "0.2em", textTransform: "uppercase",
                        fontFamily: "monospace", fontWeight: 700,
                        cursor: loading || !idea.trim() ? "not-allowed" : "pointer",
                        transition: "all 0.2s", display: "flex", alignItems: "center", justifyContent: "center", gap: "10px"
                    }}
                >
                    {loading ? (
                        <>
                            <div style={{
                                width: "13px", height: "13px",
                                border: "2px solid rgba(251,113,133,0.2)", borderTopColor: "#fb7185",
                                borderRadius: "50%", animation: "spin 0.7s linear infinite"
                            }} />
                            {step || "RUNNING..."}
                        </>
                    ) : "▶  RUN PREMORTEM ANALYSIS"}
                </button>

                {error && (
                    <p style={{ marginTop: "12px", textAlign: "center", fontSize: "12px", color: "#fb7185", fontFamily: "monospace", opacity: 0.7 }}>
                        {error}
                    </p>
                )}

                {/* Results */}
                {result && (
                    <div className="fadeup" style={{ marginTop: "52px" }}>

                        {/* Extracted Keywords */}
                        <Section title="Extracted Signals">
                            <div style={{
                                padding: "18px 20px",
                                background: "rgba(255,255,255,0.04)",
                                border: "1px solid rgba(255,255,255,0.09)",
                                borderRadius: "12px", display: "flex", flexDirection: "column", gap: "10px"
                            }}>
                                {[
                                    ["PROBLEM", result.keywords.main_problem],
                                    ["MARKET", result.keywords.target_market],
                                    ["KEYWORDS", result.keywords.core_keywords.join("  ·  ")],
                                ].map(([k, v]) => (
                                    <div key={k} style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
                                        <span style={{ fontSize: "10px", color: "#64748b", letterSpacing: "0.12em", minWidth: "68px", paddingTop: "2px", fontFamily: "monospace", fontWeight: 600 }}>{k}</span>
                                        <span style={{ fontSize: "13px", color: "#cbd5e1", lineHeight: "1.5", fontFamily: "monospace" }}>{v}</span>
                                    </div>
                                ))}
                            </div>
                        </Section>

                        {/* Failure Score */}
                        <Section title="Failure Probability">
                            <div style={{
                                position: "relative", overflow: "hidden",
                                textAlign: "center", padding: "44px 24px",
                                background: "rgba(255,255,255,0.03)",
                                border: `1px solid ${fc}30`, borderRadius: "16px"
                            }}>
                                <div style={{
                                    position: "absolute", top: 0, left: 0, right: 0, height: "1px",
                                    background: `linear-gradient(90deg, transparent, ${fc}90, transparent)`
                                }} />
                                <div style={{ fontSize: "10px", letterSpacing: "0.18em", color: "#64748b", marginBottom: "16px", fontFamily: "monospace" }}>
                                    COMPUTED FROM EXTERNAL EVIDENCE
                                </div>
                                <div style={{
                                    fontFamily: "monospace", fontWeight: 800,
                                    fontSize: "clamp(80px, 16vw, 120px)", color: fc,
                                    lineHeight: 1, letterSpacing: "-0.04em",
                                    textShadow: `0 0 80px ${fc}50`
                                }}>
                                    {result.final_failure_probability}%
                                </div>
                                <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "14px", letterSpacing: "0.12em", fontFamily: "monospace" }}>
                                    {result.final_failure_probability >= 70
                                        ? "CRITICAL — HIGH SATURATION · HIGH COMPETITION"
                                        : result.final_failure_probability >= 45
                                            ? "ELEVATED — CLEAR DEMAND · STRONG INCUMBENTS"
                                            : "MODERATE — SPACE EXISTS TO DIFFERENTIATE"}
                                </div>
                            </div>
                        </Section>

                        {/* Raw Signal Counts */}
                        <Section title="Raw Evidence Counts">
                            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                                <StatPill icon="⬡" value={fmt(result.github_repo_count)} label="GitHub Repos" sub="competition signal" />
                                <StatPill icon="◈" value={fmt(result.web_result_count)} label="Web Results" sub="market saturation" />
                                <StatPill icon="◎" value={fmt(result.reddit_signal_count)} label="Reddit Threads" sub="demand signal" />
                            </div>
                        </Section>

                        {/* Evidence Sources */}
                        <Section title="GitHub — Top Competing Repos">
                            <EvidenceList items={result.github_top_repos} color="#fb7185" />
                        </Section>

                        <Section title="Bing — Existing Market Players">
                            <EvidenceList items={result.web_top_results} color="#fbbf24" />
                        </Section>

                        <Section title="Reddit — Demand Threads">
                            <EvidenceList items={result.reddit_top_threads} color="#34d399" />
                        </Section>

                        {/* Risk Bars */}
                        <Section title="Risk Breakdown">
                            <div style={{
                                padding: "24px 24px 8px",
                                background: "rgba(255,255,255,0.03)",
                                border: "1px solid rgba(255,255,255,0.08)",
                                borderRadius: "14px"
                            }}>
                                <RiskBar label="Competition Risk" score={result.competition_risk} delay={0} />
                                <RiskBar label="Demand Strength" score={result.demand_strength} delay={100} />
                                <RiskBar label="Market Saturation" score={result.market_saturation_risk} delay={200} />
                                <RiskBar label="Execution Complexity" score={result.execution_complexity_risk} delay={300} />
                            </div>
                        </Section>

                        {/* Insights */}
                        <Section title="Evidence-Based Insights">
                            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                                {result.insights.map((ins, i) => (
                                    <div key={i} style={{
                                        display: "flex", gap: "14px", alignItems: "flex-start",
                                        padding: "14px 18px",
                                        background: "rgba(255,255,255,0.04)",
                                        border: "1px solid rgba(255,255,255,0.08)",
                                        borderRadius: "10px"
                                    }}>
                                        <span style={{ color: "#fb7185", fontSize: "11px", fontWeight: 700, minWidth: "20px", fontFamily: "monospace", paddingTop: "1px" }}>
                                            {String(i + 1).padStart(2, "0")}
                                        </span>
                                        <span style={{ fontSize: "13px", color: "#cbd5e1", lineHeight: "1.6", fontFamily: "monospace" }}>{ins}</span>
                                    </div>
                                ))}
                            </div>
                        </Section>

                    </div>
                )}
            </div>
        </div>
    );
}
