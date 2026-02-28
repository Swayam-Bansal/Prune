"use client";

import { useState, useEffect, useRef } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function riskColor(v) {
  if (v >= 70) return "#ff3b3b";
  if (v >= 40) return "#ffaa2a";
  return "#2ddc6f";
}

function useCountUp(target, ms = 1400) {
  const [count, setCount] = useState(0);
  const raf = useRef(null);
  useEffect(() => {
    setCount(0);
    const start = performance.now();
    function tick(now) {
      const p = Math.min((now - start) / ms, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      setCount(Math.round(ease * target));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    }
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, ms]);
  return count;
}

// CSS animation-based Fade — no JS state, no hydration mismatch
function Fade({ delay = 0, children }) {
  return (
    <div
      suppressHydrationWarning
      style={{
        animationName: "fadeUp",
        animationDuration: "0.65s",
        animationTimingFunction: "cubic-bezier(0.16, 1, 0.3, 1)",
        animationDelay: `${delay}ms`,
        animationFillMode: "both",
      }}
    >
      {children}
    </div>
  );
}

// ─── Gauge ───────────────────────────────────────────────────────────────────

function Gauge({ value }) {
  const animated = useCountUp(value, 1400);
  const color = riskColor(value);
  const r = 80,
    cx = 110,
    cy = 110;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;
  return (
    <div style={{ display: "flex", justifyContent: "center" }}>
      <svg width="220" height="220" style={{ overflow: "visible" }}>
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="#1a1a2e"
          strokeWidth="12"
        />
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{
            transform: "rotate(-90deg)",
            transformOrigin: `${cx}px ${cy}px`,
            transition: "stroke-dashoffset 1.4s cubic-bezier(0.16,1,0.3,1)",
            filter: `drop-shadow(0 0 10px ${color})`,
          }}
        />
        <text
          x={cx}
          y={cy - 8}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={color}
          fontSize="38"
          fontWeight="700"
          fontFamily="Geist Mono, monospace"
          style={{ filter: `drop-shadow(0 0 8px ${color})` }}
        >
          {animated}%
        </text>
        <text
          x={cx}
          y={cy + 22}
          textAnchor="middle"
          fill="#9a9aaa"
          fontSize="10"
          fontFamily="Geist Mono, monospace"
          letterSpacing="3"
        >
          FAILURE RISK
        </text>
      </svg>
    </div>
  );
}

// ─── Signal Card ─────────────────────────────────────────────────────────────

function SignalCard({ icon, num, label, color }) {
  const animated = useCountUp(num, 1600);
  return (
    <div
      style={{
        position: "relative",
        flex: 1,
        minWidth: "140px",
        background: "#0c0c18",
        border: "1px solid #1a1a2e",
        borderRadius: "20px",
        padding: "28px 20px",
        textAlign: "center",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "8px",
          left: "50%",
          transform: "translateX(-50%)",
          width: "80px",
          height: "80px",
          background: color,
          borderRadius: "50%",
          filter: "blur(32px)",
          opacity: 0.12,
          pointerEvents: "none",
        }}
      />
      <div style={{ fontSize: "26px", marginBottom: "10px" }}>{icon}</div>
      <div
        style={{
          fontSize: "30px",
          fontWeight: "700",
          fontFamily: "Geist Mono, monospace",
          color,
          marginBottom: "6px",
        }}
      >
        {animated.toLocaleString()}
      </div>
      <div
        style={{
          fontSize: "11px",
          color: "#c0c0d0",
          fontFamily: "Geist Mono, monospace",
          letterSpacing: "1px",
        }}
      >
        {label}
      </div>
    </div>
  );
}

// ─── Bar Indicator ───────────────────────────────────────────────────────────

function BarIndicator({ label, value }) {
  const [w, setW] = useState("0%");
  const color = riskColor(value);
  useEffect(() => {
    const t = setTimeout(() => setW(`${value}%`), 150);
    return () => clearTimeout(t);
  }, [value]);
  return (
    <div style={{ marginBottom: "22px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "8px",
        }}
      >
        <span
          style={{
            fontSize: "10px",
            textTransform: "uppercase",
            letterSpacing: "2px",
            color: "#b0b0c0",
            fontFamily: "Geist Mono, monospace",
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: "14px",
            fontWeight: "600",
            fontFamily: "Geist Mono, monospace",
            color,
          }}
        >
          {value}
        </span>
      </div>
      <div
        style={{
          height: "7px",
          background: "#1a1a2e",
          borderRadius: "4px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: w,
            height: "100%",
            background: color,
            borderRadius: "4px",
            transition: "width 1.2s cubic-bezier(0.16,1,0.3,1)",
            boxShadow: `0 0 8px ${color}77`,
          }}
        />
      </div>
    </div>
  );
}

// ─── Similar Startup Card ─────────────────────────────────────────────────────

function StartupCard({ name, desc, url, stage, similarity }) {
  return (
    <div
      style={{
        flex: "1 1 200px",
        background: "#0c0c18",
        border: "1px solid #1a1a2e",
        borderRadius: "16px",
        padding: "22px",
        display: "flex",
        flexDirection: "column",
        gap: "10px",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
        }}
      >
        <span
          style={{
            fontSize: "15px",
            fontWeight: "600",
            fontFamily: "Outfit, sans-serif",
            color: "#e8e8f0",
          }}
        >
          {name}
        </span>
        <span
          style={{
            fontSize: "10px",
            fontFamily: "Geist Mono, monospace",
            background: "rgba(99,102,241,0.1)",
            border: "1px solid rgba(99,102,241,0.2)",
            borderRadius: "4px",
            padding: "2px 8px",
            color: "#818cf8",
            flexShrink: 0,
          }}
        >
          {stage}
        </span>
      </div>

      {/* Description */}
      <p
        style={{
          fontSize: "13px",
          color: "#c0c0d0",
          lineHeight: "1.6",
          fontFamily: "Outfit, sans-serif",
          margin: 0,
        }}
      >
        {desc}
      </p>

      {/* Footer row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: "auto",
          paddingTop: "10px",
          borderTop: "1px solid #141425",
        }}
      >
        <span
          style={{
            fontSize: "11px",
            fontFamily: "Geist Mono, monospace",
            color: "#9a9aaa",
          }}
        >
          {similarity}% match
        </span>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            fontSize: "11px",
            fontFamily: "Geist Mono, monospace",
            color: "#7dd3fc",
            textDecoration: "none",
            letterSpacing: "0.5px",
          }}
        >
          Visit →
        </a>
      </div>
    </div>
  );
}

// ─── Reddit Thread Card ───────────────────────────────────────────────────────

function RedditCard({
  title,
  url,
  subreddit,
  upvotes,
  comments,
  similarity,
  pain_points,
  competition_signal,
}) {
  const sigColor = competition_signal === "High" ? "#ff3b3b" : "#ffaa2a";
  return (
    <div
      style={{
        background: "#0c0c18",
        border: "1px solid #1a1a2e",
        borderRadius: "16px",
        padding: "22px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
      }}
    >
      {/* Top meta */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <span
          style={{
            fontSize: "11px",
            fontFamily: "Geist Mono, monospace",
            background: "rgba(253,186,116,0.08)",
            border: "1px solid rgba(253,186,116,0.2)",
            borderRadius: "4px",
            padding: "2px 10px",
            color: "#fdba74",
          }}
        >
          {subreddit}
        </span>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <span
            style={{
              fontSize: "11px",
              fontFamily: "Geist Mono, monospace",
              color: "#9a9aaa",
            }}
          >
            ↑ {upvotes.toLocaleString()}
          </span>
          <span
            style={{
              fontSize: "11px",
              fontFamily: "Geist Mono, monospace",
              color: "#9a9aaa",
            }}
          >
            💬 {comments}
          </span>
          <span
            style={{
              fontSize: "11px",
              fontFamily: "Geist Mono, monospace",
              color: "#2ddc6f",
              background: "rgba(45,220,111,0.08)",
              border: "1px solid rgba(45,220,111,0.2)",
              borderRadius: "4px",
              padding: "2px 8px",
            }}
          >
            {similarity}% match
          </span>
        </div>
      </div>

      {/* Thread title */}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          fontSize: "14px",
          fontFamily: "Outfit, sans-serif",
          color: "#c8c8d8",
          lineHeight: "1.5",
          textDecoration: "none",
        }}
      >
        "{title}"
      </a>

      {/* Pain points */}
      <div>
        <div
          style={{
            fontSize: "10px",
            fontFamily: "Geist Mono, monospace",
            color: "#9a9aaa",
            letterSpacing: "2px",
            marginBottom: "8px",
          }}
        >
          PAIN POINTS
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {pain_points.map((p, i) => (
            <div
              key={i}
              style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}
            >
              <div
                style={{
                  width: "4px",
                  height: "4px",
                  borderRadius: "50%",
                  background: "#fdba74",
                  marginTop: "7px",
                  flexShrink: 0,
                }}
              />
              <span
                style={{
                  fontSize: "12px",
                  color: "#c8c8dc",
                  fontFamily: "Outfit, sans-serif",
                  lineHeight: "1.5",
                }}
              >
                {p}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Competition signal badge */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span
          style={{
            fontSize: "10px",
            fontFamily: "Geist Mono, monospace",
            color: "#9a9aaa",
            letterSpacing: "1px",
          }}
        >
          COMPETITION SIGNAL
        </span>
        <span
          style={{
            fontSize: "10px",
            fontFamily: "Geist Mono, monospace",
            fontWeight: "600",
            background: `${sigColor}12`,
            border: `1px solid ${sigColor}33`,
            borderRadius: "4px",
            padding: "2px 10px",
            color: sigColor,
            letterSpacing: "1px",
          }}
        >
          {competition_signal.toUpperCase()}
        </span>
      </div>
    </div>
  );
}

// ─── GitHub Repo Card ─────────────────────────────────────────────────────────

function RepoCard({ name, desc, stars, language, url }) {
  const langColors = {
    Python: "#3572A5",
    TypeScript: "#3178c6",
    Go: "#00ADD8",
    Markdown: "#4a4a5a",
  };
  const langColor = langColors[language] || "#4a4a5a";
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        background: "#0c0c18",
        border: "1px solid #1a1a2e",
        borderRadius: "16px",
        padding: "20px",
        textDecoration: "none",
        transition: "border-color 0.2s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#2a2a4e")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#1a1a2e")}
    >
      {/* Repo name + stars */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "8px",
        }}
      >
        <span
          style={{
            fontSize: "13px",
            fontFamily: "Geist Mono, monospace",
            color: "#c4b5fd",
            lineHeight: "1.4",
          }}
        >
          {name}
        </span>
        <span
          style={{
            fontSize: "12px",
            fontFamily: "Geist Mono, monospace",
            color: "#b0b0c0",
            flexShrink: 0,
          }}
        >
          ★ {stars.toLocaleString()}
        </span>
      </div>

      {/* Description */}
      <p
        style={{
          fontSize: "12px",
          color: "#c0c0d0",
          lineHeight: "1.6",
          fontFamily: "Outfit, sans-serif",
          margin: 0,
        }}
      >
        {desc}
      </p>

      {/* Language tag */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: langColor,
            }}
          />
          <span
            style={{
              fontSize: "11px",
              fontFamily: "Geist Mono, monospace",
              color: "#b0b0c0",
            }}
          >
            {language}
          </span>
        </div>
        <span
          style={{
            fontSize: "11px",
            fontFamily: "Geist Mono, monospace",
            color: "#2a2a4e",
          }}
        >
          View repo →
        </span>
      </div>
    </a>
  );
}

// ─── Flowchart ───────────────────────────────────────────────────────────────

function Flowchart() {
  const nodes = [
    {
      id: "in",
      x: 18,
      y: 101,
      w: 118,
      h: 38,
      label: "Startup Idea Input",
      stroke: "#6366f1",
      fill: "#0c0c18",
      tc: "#a5b4fc",
    },
    {
      id: "kw",
      x: 182,
      y: 101,
      w: 118,
      h: 38,
      label: "Keyword Extraction",
      stroke: "#1a1a2e",
      fill: "#0c0c18",
      tc: "#e8e8f0",
    },
    {
      id: "gh",
      x: 352,
      y: 44,
      w: 112,
      h: 34,
      label: "GitHub Search",
      stroke: "#1a1a2e",
      fill: "#0c0c18",
      tc: "#e8e8f0",
    },
    {
      id: "web",
      x: 352,
      y: 101,
      w: 112,
      h: 34,
      label: "Gemini Search",
      stroke: "#1a1a2e",
      fill: "#0c0c18",
      tc: "#e8e8f0",
    },
    {
      id: "reddit",
      x: 352,
      y: 158,
      w: 112,
      h: 34,
      label: "Reddit Search",
      stroke: "#1a1a2e",
      fill: "#0c0c18",
      tc: "#e8e8f0",
    },
    {
      id: "agg",
      x: 518,
      y: 101,
      w: 118,
      h: 38,
      label: "Signal Aggregation",
      stroke: "#1a1a2e",
      fill: "#0c0c18",
      tc: "#e8e8f0",
    },
    {
      id: "score",
      x: 688,
      y: 101,
      w: 118,
      h: 38,
      label: "Deterministic Scoring",
      stroke: "#1a1a2e",
      fill: "#0c0c18",
      tc: "#e8e8f0",
    },
    {
      id: "out",
      x: 858,
      y: 101,
      w: 118,
      h: 38,
      label: "Failure Probability",
      stroke: "#2ddc6f",
      fill: "#0a1f12",
      tc: "#2ddc6f",
    },
  ];
  const lines = [
    [136, 120, 182, 120],
    [300, 120, 340, 61],
    [300, 120, 352, 118],
    [300, 120, 340, 175],
    [464, 61, 508, 112],
    [464, 118, 518, 120],
    [464, 175, 508, 128],
    [636, 120, 688, 120],
    [806, 120, 858, 120],
  ];
  return (
    <svg viewBox="0 0 1000 220" width="100%" style={{ overflow: "visible" }}>
      <defs>
        <marker
          id="arr"
          markerWidth="7"
          markerHeight="5"
          refX="7"
          refY="2.5"
          orient="auto"
        >
          <polygon points="0 0,7 2.5,0 5" fill="#2a2a3e" />
        </marker>
        <filter id="outGlow">
          <feGaussianBlur stdDeviation="3" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {lines.map(([x1, y1, x2, y2], i) => (
        <line
          key={i}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="#2a2a3e"
          strokeWidth="1.5"
          markerEnd="url(#arr)"
        />
      ))}
      {nodes.map((n) => (
        <g key={n.id}>
          <rect
            x={n.x}
            y={n.y}
            width={n.w}
            height={n.h}
            rx="8"
            ry="8"
            fill={n.fill}
            stroke={n.stroke}
            strokeWidth={n.id === "in" || n.id === "out" ? 1.5 : 1}
            style={n.id === "out" ? { filter: "url(#outGlow)" } : undefined}
          />
          <text
            x={n.x + n.w / 2}
            y={n.y + n.h / 2}
            textAnchor="middle"
            dominantBaseline="middle"
            fill={n.tc}
            fontSize="10"
            fontFamily="Geist Mono, monospace"
            fontWeight={n.id === "in" || n.id === "out" ? "600" : "400"}
          >
            {n.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

// ─── Chart Tooltip ────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#0c0c18",
        border: "1px solid #1a1a2e",
        borderRadius: "10px",
        padding: "10px 16px",
        fontFamily: "Geist Mono, monospace",
        fontSize: "12px",
      }}
    >
      <div
        style={{
          color: "#b0b0c0",
          fontSize: "10px",
          letterSpacing: "1px",
          marginBottom: "4px",
        }}
      >
        {label}
      </div>
      <div style={{ color: riskColor(payload[0].value), fontWeight: "600" }}>
        {payload[0].value}
      </div>
    </div>
  );
}

// ─── Shared styles ────────────────────────────────────────────────────────────

const CARD = {
  background: "#0c0c18",
  border: "1px solid #1a1a2e",
  borderRadius: "20px",
  padding: "32px",
  boxShadow: "0 4px 40px rgba(0,0,0,0.5)",
  marginBottom: "20px",
};

const LABEL = {
  fontSize: "10px",
  textTransform: "uppercase",
  letterSpacing: "3px",
  color: "#b0b0c0",
  fontFamily: "Geist Mono, monospace",
  marginBottom: "20px",
};

// ─── Loading ──────────────────────────────────────────────────────────────────

const BASIC_STEPS = [
  "Extracting core keywords...",
  "Searching GitHub repositories...",
  "Scanning similar startups with Gemini...",
  "Computing deterministic score...",
];

const DEEP_STEPS = [
  "Extracting core keywords...",
  "Searching GitHub repositories...",
  "Scanning similar startups with Gemini...",
  "Mining Reddit demand signals...",
  "Computing deterministic score...",
];

function LoadingView({ completedSteps = [], deepMode = false }) {
  const STEPS = deepMode ? DEEP_STEPS : BASIC_STEPS;
  const timeEstimate = deepMode
    ? "This may take 2-3 minutes..."
    : "This may take 30-60 seconds...";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "80vh",
        gap: "36px",
      }}
    >
      <div
        style={{
          width: "44px",
          height: "44px",
          borderRadius: "50%",
          border: "2px solid #1a1a2e",
          borderTop: "2px solid #6366f1",
          animation: "spin 0.8s linear infinite",
        }}
      />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "14px",
          width: "310px",
        }}
      >
        {STEPS.map((s, i) => {
          const isComplete = completedSteps.includes(i);
          const isSkipped = completedSteps.includes(`skip-${i}`);
          const isActive =
            !isComplete &&
            !isSkipped &&
            (i === 0 || completedSteps.includes(i - 1));

          return (
            <div
              key={s}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                opacity: isSkipped ? 0.4 : 1,
                transition: "opacity 0.4s ease",
              }}
            >
              <div
                style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "50%",
                  flexShrink: 0,
                  background: isComplete
                    ? "#2ddc6f"
                    : isSkipped
                      ? "#4a4a5a"
                      : "#6366f1",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "10px",
                  color: "#fff",
                  fontWeight: "700",
                  transition: "background 0.3s ease",
                  animation:
                    isActive && !isComplete && !isSkipped
                      ? "pulse 1.5s ease-in-out infinite"
                      : "none",
                  boxShadow: isComplete
                    ? "0 0 12px rgba(45, 220, 111, 0.5)"
                    : "none",
                }}
              >
                {isComplete && "✓"}
                {isSkipped && "—"}
              </div>
              <span
                style={{
                  fontSize: "12px",
                  fontFamily: "Geist Mono, monospace",
                  color: isComplete
                    ? "#2ddc6f"
                    : isSkipped
                      ? "#4a4a5a"
                      : "#a5b4fc",
                  transition: "color 0.3s ease",
                }}
              >
                {s}
              </span>
            </div>
          );
        })}
      </div>
      <div
        style={{
          fontSize: "11px",
          fontFamily: "Geist Mono, monospace",
          color: "#b0b0c0",
          letterSpacing: "1px",
          marginTop: "8px",
        }}
      >
        {timeEstimate}
      </div>
    </div>
  );
}

// ─── Input View ───────────────────────────────────────────────────────────────

function InputView({ idea, setIdea, deepMode, setDeepMode, onRun, error }) {
  const [focused, setFocused] = useState(false);
  const ready = idea.trim().length >= 10;

  return (
    <div
      style={{ maxWidth: "680px", margin: "0 auto", padding: "72px 24px 80px" }}
    >
      <div style={{ textAlign: "center", marginBottom: "28px" }}>
        <span
          style={{
            display: "inline-block",
            background: "rgba(99,102,241,0.1)",
            border: "1px solid rgba(99,102,241,0.25)",
            borderRadius: "999px",
            padding: "6px 18px",
            fontSize: "10px",
            fontFamily: "Geist Mono, monospace",
            letterSpacing: "3px",
            color: "#818cf8",
          }}
        >
          EXTERNAL MARKET RISK ENGINE
        </span>
      </div>

      <h1
        style={{
          textAlign: "center",
          fontSize: "clamp(44px, 8vw, 78px)",
          fontWeight: "300",
          lineHeight: "1",
          fontFamily: "Outfit, sans-serif",
          letterSpacing: "-2px",
          marginBottom: "18px",
        }}
      >
        Pre
        <span
          style={{
            fontWeight: "800",
            color: "#ff3b3b",
            textShadow: "0 0 32px rgba(255,59,59,0.4)",
          }}
        >
          Mortem
        </span>
      </h1>

      <p
        style={{
          textAlign: "center",
          color: "#c0c0d0",
          fontSize: "15px",
          lineHeight: "1.7",
          marginBottom: "48px",
          fontFamily: "Outfit, sans-serif",
        }}
      >
        Real signals from GitHub, Gemini &amp; Reddit.
        <br />
        Deterministic failure risk — no hallucinated scores.
      </p>

      <div
        style={{
          border: `1px solid ${focused ? "#3a3a6e" : "#1a1a2e"}`,
          borderRadius: "16px",
          overflow: "hidden",
          background: "#0c0c18",
          transition: "border-color 0.2s, box-shadow 0.2s",
          boxShadow: focused ? "0 0 0 3px rgba(99,102,241,0.07)" : "none",
          marginBottom: "14px",
        }}
      >
        <textarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={
            "Describe your startup idea...\n\nExample: A SaaS tool that uses AI to automatically\ngenerate legal contracts for freelancers."
          }
          rows={7}
          style={{
            width: "100%",
            padding: "20px 24px",
            background: "transparent",
            border: "none",
            outline: "none",
            color: "#e8e8f0",
            fontSize: "15px",
            fontFamily: "Outfit, sans-serif",
            lineHeight: "1.7",
            resize: "vertical",
          }}
        />
      </div>

      {error && (
        <div
          style={{
            background: "rgba(255,59,59,0.07)",
            border: "1px solid rgba(255,59,59,0.2)",
            borderRadius: "10px",
            padding: "12px 16px",
            marginBottom: "14px",
            fontSize: "13px",
            fontFamily: "Geist Mono, monospace",
            color: "#ff6b6b",
          }}
        >
          {error}
        </div>
      )}

      <div
        style={{
          background: "#0c0c18",
          border: "1px solid #1a1a2e",
          borderRadius: "12px",
          padding: "16px 20px",
          marginBottom: "14px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
        }}
      >
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontSize: "13px",
              fontWeight: "600",
              fontFamily: "Outfit, sans-serif",
              color: "#e8e8f0",
              marginBottom: "4px",
            }}
          >
            {deepMode ? "🔍 Deep Search Mode" : "⚡ Basic Search Mode"}
          </div>
          <div
            style={{
              fontSize: "11px",
              fontFamily: "Geist Mono, monospace",
              color: "#c0c0d0",
              lineHeight: "1.5",
            }}
          >
            {deepMode
              ? "GitHub + Gemini + Reddit analysis (2-3 mins)"
              : "GitHub + Gemini search only (~30 seconds)"}
          </div>
        </div>
        <button
          onClick={() => setDeepMode(!deepMode)}
          style={{
            position: "relative",
            width: "52px",
            height: "28px",
            background: deepMode ? "#6366f1" : "#1a1a2e",
            border: "none",
            borderRadius: "14px",
            cursor: "pointer",
            transition: "background 0.3s",
            flexShrink: 0,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "3px",
              left: deepMode ? "26px" : "3px",
              width: "22px",
              height: "22px",
              background: "#fff",
              borderRadius: "50%",
              transition: "left 0.3s",
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
            }}
          />
        </button>
      </div>

      <button
        onClick={onRun}
        disabled={!ready}
        style={{
          width: "100%",
          padding: "16px",
          background: ready ? "#6366f1" : "#111128",
          border: `1px solid ${ready ? "#6366f1" : "#1a1a2e"}`,
          borderRadius: "12px",
          color: ready ? "#fff" : "#2a2a4e",
          fontSize: "15px",
          fontWeight: "600",
          fontFamily: "Outfit, sans-serif",
          cursor: ready ? "pointer" : "not-allowed",
          transition: "all 0.2s",
          boxShadow: ready ? "0 4px 24px rgba(99,102,241,0.3)" : "none",
        }}
      >
        Run PreMortem Analysis
      </button>

      <p
        style={{
          textAlign: "center",
          marginTop: "18px",
          fontSize: "10px",
          fontFamily: "Geist Mono, monospace",
          color: "#8a8a9e",
          letterSpacing: "2px",
        }}
      >
        POWERED BY: GEMINI · GITHUB · REDDIT APIs
      </p>
    </div>
  );
}

// ─── Results View ─────────────────────────────────────────────────────────────

function ResultsView({ onReset, data }) {
  const failureProb = data.final_failure_probability;
  const failColor = riskColor(failureProb);
  const failLabel =
    failureProb >= 70
      ? "HIGH RISK"
      : failureProb >= 40
        ? "MODERATE RISK"
        : "LOW RISK";

  const risks = [
    { name: "Comp", value: data.competition_risk },
    { name: "Saturation", value: data.market_saturation_risk },
    { name: "Demand", value: data.demand_strength },
    { name: "Execution", value: data.execution_complexity_risk },
  ];

  const signals = [
    {
      icon: "⚡",
      num: data.github_repo_count,
      label: "GITHUB REPOS",
      color: "#c4b5fd",
    },
    {
      icon: "🌐",
      num: data.web_result_count,
      label: "WEB RESULTS",
      color: "#818cf8",
    },
    {
      icon: "💬",
      num: data.reddit_signal_count,
      label: "REDDIT SIGNALS",
      color: "#fdba74",
    },
  ];

  const githubRepos = (data.top_repos || []).map((r) => ({
    name: r.name,
    desc: r.description || "",
    stars: r.stars,
    language: r.language || "",
    url: r.url,
  }));

  return (
    <div
      style={{ maxWidth: "960px", margin: "0 auto", padding: "48px 24px 80px" }}
    >
      {/* ── Top bar ── */}
      <Fade delay={0}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "28px",
            flexWrap: "wrap",
            gap: "14px",
          }}
        >
          <div>
            <span
              style={{
                display: "inline-block",
                background: "rgba(99,102,241,0.1)",
                border: "1px solid rgba(99,102,241,0.25)",
                borderRadius: "999px",
                padding: "5px 14px",
                fontSize: "10px",
                fontFamily: "Geist Mono, monospace",
                letterSpacing: "3px",
                color: "#818cf8",
              }}
            >
              EXTERNAL MARKET RISK ENGINE
            </span>
            <h1
              style={{
                fontSize: "clamp(28px, 5vw, 46px)",
                fontWeight: "300",
                lineHeight: "1.1",
                fontFamily: "Outfit, sans-serif",
                letterSpacing: "-1px",
                marginTop: "10px",
              }}
            >
              Pre
              <span
                style={{
                  fontWeight: "800",
                  color: "#ff3b3b",
                  textShadow: "0 0 20px rgba(255,59,59,0.35)",
                }}
              >
                Mortem
              </span>
            </h1>
          </div>
          <button
            onClick={onReset}
            style={{
              background: "transparent",
              border: "1px solid #1a1a2e",
              borderRadius: "10px",
              padding: "10px 18px",
              color: "#b0b0c0",
              fontSize: "12px",
              fontFamily: "Geist Mono, monospace",
              cursor: "pointer",
              letterSpacing: "1px",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "#3a3a5e";
              e.currentTarget.style.color = "#a5b4fc";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "#1a1a2e";
              e.currentTarget.style.color = "#4a4a6a";
            }}
          >
            ← NEW ANALYSIS
          </button>
        </div>
      </Fade>

      {/* ── Keywords ── */}
      <Fade delay={60}>
        <div style={CARD}>
          <div style={LABEL}>Extracted Signals</div>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "8px",
              alignItems: "center",
            }}
          >
            {[
              { tag: "PROBLEM", val: data.keywords.main_problem },
              { tag: "MARKET", val: data.keywords.target_market },
            ].map(({ tag, val }) => (
              <span
                key={tag}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <span
                  style={{
                    fontSize: "10px",
                    fontFamily: "Geist Mono, monospace",
                    color: "#9a9aaa",
                    letterSpacing: "1px",
                  }}
                >
                  {tag}
                </span>
                <span
                  style={{
                    background: "rgba(99,102,241,0.08)",
                    border: "1px solid rgba(99,102,241,0.18)",
                    borderRadius: "6px",
                    padding: "4px 12px",
                    fontSize: "12px",
                    fontFamily: "Geist Mono, monospace",
                    color: "#a5b4fc",
                  }}
                >
                  {val}
                </span>
              </span>
            ))}
            <span
              style={{
                fontSize: "10px",
                fontFamily: "Geist Mono, monospace",
                color: "#9a9aaa",
                letterSpacing: "1px",
                marginLeft: "4px",
              }}
            >
              KEYWORDS
            </span>
            {(data.keywords.core_keywords || []).map((kw) => (
              <span
                key={kw}
                style={{
                  background: "#0f0f1e",
                  border: "1px solid #1a1a2e",
                  borderRadius: "6px",
                  padding: "4px 10px",
                  fontSize: "12px",
                  fontFamily: "Geist Mono, monospace",
                  color: "#b8b8cc",
                }}
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      </Fade>

      {/* ── Failure Gauge ── */}
      <Fade delay={100}>
        <div style={{ ...CARD, textAlign: "center" }}>
          <div style={LABEL}>Failure Probability</div>
          <Gauge value={failureProb} />
          <div style={{ marginTop: "16px" }}>
            <span
              style={{
                display: "inline-block",
                background: `${failColor}14`,
                border: `1px solid ${failColor}44`,
                borderRadius: "999px",
                padding: "6px 22px",
                fontSize: "11px",
                fontFamily: "Geist Mono, monospace",
                letterSpacing: "2px",
                color: failColor,
                fontWeight: "600",
                textShadow: `0 0 12px ${failColor}66`,
              }}
            >
              {failLabel}
            </span>
          </div>
        </div>
      </Fade>

      {/* ── Signal Cards ── */}
      <Fade delay={150}>
        <div
          style={{
            display: "flex",
            gap: "16px",
            flexWrap: "wrap",
            marginBottom: "20px",
          }}
        >
          {signals.map((s) => (
            <SignalCard
              key={s.label}
              icon={s.icon}
              num={s.num}
              label={s.label}
              color={s.color}
            />
          ))}
        </div>
      </Fade>

      {/* ── Risk Bars + Chart ── */}
      <Fade delay={200}>
        <div style={CARD}>
          <div style={LABEL}>Risk Factor Breakdown</div>
          <BarIndicator label="Competition Risk" value={risks[0].value} />
          <BarIndicator label="Market Saturation" value={risks[1].value} />
          <BarIndicator label="Demand Strength" value={risks[2].value} />
          <BarIndicator label="Execution Complexity" value={risks[3].value} />
          <div style={{ marginTop: "32px" }}>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={risks}
                margin={{ top: 0, right: 0, left: -20, bottom: 0 }}
              >
                <XAxis
                  dataKey="name"
                  tick={{
                    fill: "#c0c0d0",
                    fontFamily: "Geist Mono, monospace",
                    fontSize: 10,
                  }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{
                    fill: "#b0b0c0",
                    fontFamily: "Geist Mono, monospace",
                    fontSize: 10,
                  }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  content={<ChartTooltip />}
                  cursor={{ fill: "rgba(255,255,255,0.02)" }}
                />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {risks.map((entry) => (
                    <Cell key={entry.name} fill={riskColor(entry.value)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div
            style={{
              display: "flex",
              gap: "24px",
              justifyContent: "center",
              marginTop: "16px",
            }}
          >
            {[
              ["#ff3b3b", "High (≥70)"],
              ["#ffaa2a", "Moderate (≥40)"],
              ["#2ddc6f", "Low (<40)"],
            ].map(([c, l]) => (
              <div
                key={l}
                style={{ display: "flex", alignItems: "center", gap: "7px" }}
              >
                <div
                  style={{
                    width: "9px",
                    height: "9px",
                    borderRadius: "2px",
                    background: c,
                  }}
                />
                <span
                  style={{
                    fontSize: "10px",
                    fontFamily: "Geist Mono, monospace",
                    color: "#c0c0d0",
                  }}
                >
                  {l}
                </span>
              </div>
            ))}
          </div>
        </div>
      </Fade>

      {/* ── Similar Startups ── */}
      {data.similar_startups && data.similar_startups.length > 0 && (
        <Fade delay={260}>
          <div style={CARD}>
            <div style={LABEL}>Similar Startups Found</div>
            <p
              style={{
                fontSize: "12px",
                color: "#b0b0c0",
                fontFamily: "Geist Mono, monospace",
                marginBottom: "20px",
                letterSpacing: "0.3px",
              }}
            >
              Identified via Gemini search — direct competitors in your space
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "14px" }}>
              {data.similar_startups.map((s) => (
                <StartupCard key={s.name} {...s} />
              ))}
            </div>
          </div>
        </Fade>
      )}

      {/* ── Reddit Intelligence ── */}
      {data.reddit_threads && data.reddit_threads.length > 0 && (
        <Fade delay={320}>
          <div style={CARD}>
            <div style={LABEL}>Reddit Intelligence</div>
            <p
              style={{
                fontSize: "12px",
                color: "#b0b0c0",
                fontFamily: "Geist Mono, monospace",
                marginBottom: "20px",
                letterSpacing: "0.3px",
              }}
            >
              Real user discussions — pain points and demand signals
            </p>
            <div
              style={{ display: "flex", flexDirection: "column", gap: "14px" }}
            >
              {data.reddit_threads.map((t) => (
                <RedditCard key={t.title} {...t} />
              ))}
            </div>
          </div>
        </Fade>
      )}

      {/* ── GitHub Repos ── */}
      <Fade delay={380}>
        <div style={CARD}>
          <div style={LABEL}>GitHub Competition Map</div>
          <p
            style={{
              fontSize: "12px",
              color: "#b0b0c0",
              fontFamily: "Geist Mono, monospace",
              marginBottom: "20px",
              letterSpacing: "0.3px",
            }}
          >
            Open-source repositories competing in this problem space
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: "14px",
            }}
          >
            {githubRepos.map((r) => (
              <RepoCard key={r.name} {...r} />
            ))}
          </div>
        </div>
      </Fade>

      {/* ── Insights ── */}
      <Fade delay={440}>
        <div style={CARD}>
          <div style={LABEL}>Evidence-Based Insights</div>
          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            {(data.insights || []).map((insight, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: "14px",
                  alignItems: "flex-start",
                }}
              >
                <div
                  style={{
                    width: "6px",
                    height: "6px",
                    borderRadius: "50%",
                    flexShrink: 0,
                    background: "#6366f1",
                    marginTop: "8px",
                  }}
                />
                <p
                  style={{
                    fontSize: "14px",
                    color: "#b8b8cc",
                    lineHeight: "1.65",
                    fontFamily: "Outfit, sans-serif",
                    margin: 0,
                  }}
                >
                  {insight}
                </p>
              </div>
            ))}
          </div>
        </div>
      </Fade>

      {/* ── Pipeline Flowchart ── */}
      <Fade delay={500}>
        <div style={CARD}>
          <div style={LABEL}>Analysis Pipeline</div>
          <p
            style={{
              fontSize: "12px",
              color: "#9a9aaa",
              fontFamily: "Geist Mono, monospace",
              marginBottom: "24px",
              letterSpacing: "0.5px",
            }}
          >
            End-to-end signal collection → deterministic scoring
          </p>
          <div style={{ overflowX: "auto" }}>
            <Flowchart />
          </div>
        </div>
      </Fade>

      {/* ── Footer ── */}
      <Fade delay={560}>
        <div
          style={{
            textAlign: "center",
            paddingTop: "8px",
            fontSize: "10px",
            fontFamily: "Geist Mono, monospace",
            color: "#7a7a8e",
            letterSpacing: "3px",
          }}
        >
          PREMORTEM · DETERMINISTIC RISK ENGINE · 2026
        </div>
      </Fade>
    </div>
  );
}

// ─── Root ─────────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [view, setView] = useState("input");
  const [idea, setIdea] = useState("");
  const [deepMode, setDeepMode] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [completedSteps, setCompletedSteps] = useState([]);

  async function runAnalysis() {
    if (idea.trim().length < 10) return;
    setError(null);
    setView("loading");
    setCompletedSteps([]);

    try {
      const res = await fetch("/api/analyze-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea: idea.trim(), deep_mode: deepMode }),
      });

      if (!res.ok) {
        setError("Analysis failed. Please try again.");
        setView("input");
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));

            if (data.error) {
              setError(data.error);
              setView("input");
              return;
            }

            if (data.step === "done") {
              setData(data.result);
              setView("results");
            } else if (
              typeof data.step === "number" &&
              data.status === "complete"
            ) {
              setCompletedSteps((prev) => [...prev, data.step]);
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || "Network error. Please try again.");
      setView("input");
    }
  }

  return (
    <main style={{ minHeight: "100vh" }}>
      {view === "input" && (
        <InputView
          idea={idea}
          setIdea={setIdea}
          deepMode={deepMode}
          setDeepMode={setDeepMode}
          onRun={runAnalysis}
          error={error}
        />
      )}
      {view === "loading" && (
        <LoadingView completedSteps={completedSteps} deepMode={deepMode} />
      )}
      {view === "results" && data && (
        <ResultsView
          onReset={() => {
            setView("input");
            setIdea("");
            setDeepMode(false);
            setData(null);
            setCompletedSteps([]);
          }}
          data={data}
        />
      )}
    </main>
  );
}
