"""
PreMortem Dashboard — Beautiful Streamlit UI
=============================================
Run with:  streamlit run dashboard.py

Talks to the FastAPI backend at http://127.0.0.1:8000.
Supports both mock data preview and live analysis.
"""

import streamlit as st
import httpx
import json
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from mock_data import SAMPLE_INPUTS

# ── Page config ─────────────────────────────────────────
st.set_page_config(
    page_title="PreMortem — Startup Signal Engine",
    page_icon="💀",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://127.0.0.1:8000"
TIMEOUT = 600  # 10 min for long analyses

# ── Custom CSS ──────────────────────────────────────────
st.markdown("""
<style>
    /* Global */
    .stApp { background-color: #0e1117; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1d23 0%, #21252b 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px 20px;
    }
    div[data-testid="stMetric"] label {
        color: #8b949e !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* Thread cards */
    .thread-card {
        background: linear-gradient(135deg, #161b22 0%, #1a1f27 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        transition: border-color 0.2s;
    }
    .thread-card:hover { border-color: #58a6ff; }
    .thread-title { color: #58a6ff; font-size: 1.05rem; font-weight: 600; margin-bottom: 8px; }
    .thread-meta { color: #8b949e; font-size: 0.82rem; margin-bottom: 10px; }
    .thread-insight { color: #c9d1d9; font-size: 0.92rem; line-height: 1.5; }
    .thread-quote {
        border-left: 3px solid #58a6ff;
        padding-left: 12px;
        margin: 10px 0;
        color: #8b949e;
        font-style: italic;
        font-size: 0.88rem;
    }

    /* Signal badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-pain { background: #3d1f1f; color: #f85149; border: 1px solid #f8514966; }
    .badge-demand { background: #1f3d1f; color: #3fb950; border: 1px solid #3fb95066; }
    .badge-competition { background: #3d3d1f; color: #d29922; border: 1px solid #d2992266; }
    .badge-skepticism { background: #1f2d3d; color: #58a6ff; border: 1px solid #58a6ff66; }

    /* Section headers */
    .section-header {
        color: #f0f6fc;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 30px 0 15px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #21262d;
    }

    /* Score ring label */
    .score-label { text-align: center; color: #8b949e; font-size: 0.85rem; margin-top: 4px; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #161b22 !important;
        border-right: 1px solid #21262d;
    }

    /* Tabs */
    button[data-baseweb="tab"] { color: #8b949e !important; font-weight: 600 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #58a6ff !important; }
</style>
""", unsafe_allow_html=True)


# ── Helper functions ────────────────────────────────────
def signal_badge(signal_type: str) -> str:
    colors = {
        "pain_point": "pain",
        "demand": "demand",
        "competition": "competition",
        "skepticism": "skepticism",
    }
    cls = colors.get(signal_type, "demand")
    label = signal_type.replace("_", " ").title()
    return f'<span class="badge badge-{cls}">{label}</span>'


def score_gauge(value: int, title: str, color: str) -> go.Figure:
    """Create a radial gauge chart for a score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 14, "color": "#8b949e"}},
        number={"font": {"size": 36, "color": "#f0f6fc"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "#21262d",
                     "tickfont": {"color": "#484f58"}},
            "bar": {"color": color, "thickness": 0.7},
            "bgcolor": "#21262d",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 33], "color": "rgba(22,27,34,0.25)"},
                {"range": [33, 66], "color": "rgba(22,27,34,0.37)"},
                {"range": [66, 100], "color": "rgba(22,27,34,0.50)"},
            ],
        },
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f0f6fc"},
    )
    return fig


def coverage_chart(coverage: dict) -> go.Figure:
    """Create a radar chart for signal coverage."""
    counts = coverage.get("counts", {})
    categories = list(counts.keys())
    values = list(counts.values())
    # Close the polygon
    categories.append(categories[0])
    values.append(values[0])

    labels = [c.replace("_", " ").title() for c in categories]

    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        fillcolor="rgba(88, 166, 255, 0.15)",
        line=dict(color="#58a6ff", width=2),
        marker=dict(size=8, color="#58a6ff"),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, gridcolor="#21262d",
                            tickfont={"color": "#484f58"}),
            angularaxis=dict(gridcolor="#21262d", tickfont={
                             "color": "#8b949e", "size": 12}),
        ),
        height=350,
        margin=dict(l=60, r=60, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def subreddit_chart(threads: list[dict]) -> go.Figure:
    """Bar chart of threads by subreddit."""
    subs = {}
    for t in threads:
        sub = t.get("subreddit", "unknown")
        subs[sub] = subs.get(sub, 0) + 1
    subs_sorted = sorted(subs.items(), key=lambda x: x[1], reverse=True)[:15]

    fig = go.Figure(go.Bar(
        x=[s[1] for s in subs_sorted],
        y=[s[0] for s in subs_sorted],
        orientation="h",
        marker=dict(color="#58a6ff", line=dict(width=0)),
    ))
    fig.update_layout(
        height=max(250, len(subs_sorted) * 30 + 60),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#21262d", tickfont={"color": "#8b949e"}),
        yaxis=dict(tickfont={"color": "#c9d1d9"}, autorange="reversed"),
        bargap=0.3,
    )
    return fig


def signal_distribution_chart(threads: list[dict]) -> go.Figure:
    """Donut chart of signal types."""
    types = {}
    for t in threads:
        st = t.get("signal_type", "other")
        types[st] = types.get(st, 0) + 1

    colors_map = {
        "pain_point": "#f85149",
        "demand": "#3fb950",
        "competition": "#d29922",
        "skepticism": "#58a6ff",
    }

    labels = [k.replace("_", " ").title() for k in types.keys()]
    values = list(types.values())
    colors = [colors_map.get(k, "#8b949e") for k in types.keys()]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0e1117", width=2)),
        textfont=dict(color="#f0f6fc", size=12),
        hovertemplate="<b>%{label}</b><br>%{value} threads<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="#c9d1d9", size=11)),
        showlegend=True,
    )
    return fig


def render_thread_card(thread: dict, idx: int):
    """Render a single thread as a styled card."""
    title = thread.get("title", "Untitled")
    url = thread.get("url", "")
    subreddit = thread.get("subreddit", "")
    score = thread.get("score", 0)
    num_comments = thread.get("num_comments", 0)
    relevance = thread.get("relevance_score", 0)
    signal_type = thread.get("signal_type", "")
    insight = thread.get("insight", "")
    quotes = thread.get("key_quotes", [])
    competitors = thread.get("competing_products", [])
    needs = thread.get("unmet_needs", [])

    badge = signal_badge(signal_type)
    relevance_color = "#3fb950" if relevance >= 80 else (
        "#d29922" if relevance >= 60 else "#8b949e")

    quotes_html = ""
    for q in quotes[:2]:
        quotes_html += f'<div class="thread-quote">"{q}"</div>'

    competitors_html = ""
    if competitors:
        comp_tags = " · ".join(competitors[:5])
        competitors_html = f'<div style="color:#d29922;font-size:0.82rem;margin-top:8px;">⚔️ Competitors: {comp_tags}</div>'

    needs_html = ""
    if needs:
        needs_tags = " · ".join(needs[:3])
        needs_html = f'<div style="color:#3fb950;font-size:0.82rem;margin-top:4px;">💡 Gaps: {needs_tags}</div>'

    card_html = f"""
    <div class="thread-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div class="thread-title">
                <a href="{url}" target="_blank" style="color:#58a6ff;text-decoration:none;">{title}</a>
            </div>
            <span style="color:{relevance_color};font-weight:700;font-size:1.1rem;">{relevance}%</span>
        </div>
        <div class="thread-meta">
            {badge} &nbsp;·&nbsp; {subreddit} &nbsp;·&nbsp; ⬆️ {score:,} &nbsp;·&nbsp; 💬 {num_comments:,}
        </div>
        <div class="thread-insight">{insight}</div>
        {quotes_html}
        {competitors_html}
        {needs_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def check_backend() -> bool:
    """Check if the FastAPI backend is running."""
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ── Sidebar ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💀 PreMortem")
    st.markdown("##### Agentic Market Signal Engine")
    st.markdown("---")

    mode = st.radio(
        "Mode",
        ["🔍 Live Analysis", "🧪 Mock Preview"],
        index=0,
        help="Live Analysis calls the real engine (OpenAI + Reddit). Mock Preview uses sample data.",
    )

    st.markdown("---")
    st.markdown("##### 💡 Sample Ideas")
    st.markdown("Click to auto-fill the form:")

    for i, sample in enumerate(SAMPLE_INPUTS):
        if st.button(
            f"{'📋'} {sample['idea'][:45]}{'...' if len(sample['idea']) > 45 else ''}",
            key=f"sample_{i}",
            use_container_width=True,
        ):
            st.session_state["idea"] = sample["idea"]
            st.session_state["problem"] = sample["problem"]
            st.session_state["solution"] = sample["solution"]
            st.session_state["product_specs"] = sample.get("product_specs", "")

    st.markdown("---")
    backend_ok = check_backend()
    if backend_ok:
        st.success("✅ Backend connected")
    else:
        st.error("❌ Backend offline — start with `uvicorn main:app --reload`")

    st.markdown("---")
    st.caption("PreMortem v1.0 · Built with Streamlit + FastAPI")


# ── Main content ────────────────────────────────────────
st.markdown("# 💀 PreMortem")
st.markdown("### Will your startup idea survive contact with reality?")
st.markdown("Enter your startup idea below and let the engine scan Reddit for real market signals — pain points, demand, competition, and skepticism.")
st.markdown("")

# ── Input form ──────────────────────────────────────────
with st.form("idea_form"):
    col1, col2 = st.columns(2)
    with col1:
        idea = st.text_input(
            "💡 Startup Idea",
            value=st.session_state.get("idea", ""),
            placeholder="e.g. AI-powered resume screener for small businesses",
        )
        problem = st.text_area(
            "🔥 Problem",
            value=st.session_state.get("problem", ""),
            placeholder="What pain point does it solve?",
            height=100,
        )
    with col2:
        solution = st.text_area(
            "🛠️ Solution",
            value=st.session_state.get("solution", ""),
            placeholder="How does the product solve it?",
            height=100,
        )
        product_specs = st.text_area(
            "📐 Product Specs (optional)",
            value=st.session_state.get("product_specs", ""),
            placeholder="Tech stack, pricing, platform, etc.",
            height=100,
        )

    submitted = st.form_submit_button(
        "🚀 Analyze This Idea", use_container_width=True, type="primary")

# ── Handle submission ───────────────────────────────────
if submitted and idea and problem and solution:
    if mode == "🧪 Mock Preview":
        # Load mock data directly
        with st.spinner("Loading mock data..."):
            try:
                resp = httpx.get(f"{API_BASE}/mock/analyze", timeout=10)
                if resp.status_code == 200:
                    st.session_state["result"] = resp.json()
                else:
                    st.error(f"Mock endpoint returned {resp.status_code}")
            except Exception as e:
                st.error(f"Could not reach backend: {e}")

    elif mode == "🔍 Live Analysis":
        if not backend_ok:
            st.error(
                "Backend is offline. Start it with `uvicorn main:app --reload --port 8000`")
        else:
            progress_bar = st.progress(0, text="Starting analysis...")
            status_placeholder = st.empty()

            try:
                payload = {
                    "idea": idea,
                    "problem": problem,
                    "solution": solution,
                    "product_specs": product_specs or "",
                }

                # Use streaming endpoint for live status updates
                with httpx.Client(timeout=TIMEOUT) as client:
                    with client.stream("POST", f"{API_BASE}/analyze/stream", json=payload) as response:
                        full_result = None
                        step = 0
                        stage_map = {
                            "generating_queries": (0.05, "🧠 Generating search queries..."),
                            "searching": (0.20, "🔍 Searching Reddit..."),
                            "analyzing": (0.40, "🤖 Analyzing threads with GPT-4o..."),
                            "evaluation": (0.60, "📊 Evaluating signal coverage..."),
                            "refining_queries": (0.65, "🔄 Refining queries for gaps..."),
                            "synthesizing": (0.85, "📝 Writing final report..."),
                            "complete": (1.0, "✅ Analysis complete!"),
                        }

                        for line in response.iter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = json.loads(line[6:])

                            if data.get("type") == "status":
                                stage = data.get("stage", "")
                                detail = data.get("detail", "")
                                pct, label = stage_map.get(stage, (None, None))
                                if pct is not None:
                                    progress_bar.progress(pct, text=label)
                                status_placeholder.caption(f"⏳ {detail}")

                            elif data.get("type") == "result":
                                full_result = data.get("data", {})

                            elif data.get("type") == "error":
                                st.error(
                                    f"Engine error: {data.get('detail', 'unknown')}")

                if full_result:
                    # Convert to the same shape as the /analyze JSON response
                    from models import SignalThread, Scores
                    threads = full_result.get("threads", [])
                    scores_raw = full_result.get("scores", {})
                    st.session_state["result"] = {
                        "report": full_result.get("report", ""),
                        "scores": scores_raw,
                        "threads": threads,
                        "iterations": full_result.get("iterations", 0),
                        "queries_used": full_result.get("queries_used", []),
                        "coverage": full_result.get("coverage", {}),
                        "elapsed_seconds": full_result.get("elapsed_seconds", 0),
                    }
                    progress_bar.progress(1.0, text="✅ Done!")
                    status_placeholder.empty()

            except httpx.ReadTimeout:
                st.error(
                    "Analysis timed out (>10 min). The idea may be too broad — try being more specific.")
            except Exception as e:
                st.error(f"Error: {e}")

elif submitted:
    st.warning("Please fill in at least the Idea, Problem, and Solution fields.")

# ── Results display ─────────────────────────────────────
if "result" in st.session_state and st.session_state["result"]:
    result = st.session_state["result"]
    scores = result.get("scores", {})
    threads = result.get("threads", [])
    coverage = result.get("coverage", {})
    report = result.get("report", "")
    iterations = result.get("iterations", 0)
    elapsed = result.get("elapsed_seconds", 0)
    queries_used = result.get("queries_used", [])

    st.markdown("---")

    # ── Top metrics row ─────────────────────────────────
    st.markdown('<div class="section-header">📊 Risk Scores</div>',
                unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Demand Score", f"{scores.get('demand_score', 0)}/100")
    with m2:
        st.metric("Pain Validation", f"{scores.get('pain_validation', 0)}/100")
    with m3:
        st.metric("Competition Risk",
                  f"{scores.get('competition_risk', 0)}/100")
    with m4:
        failure_prob = scores.get("overall_failure_probability", 0)
        st.metric("Failure Probability", f"{failure_prob}%",
                  delta=f"{'High' if failure_prob > 60 else 'Medium' if failure_prob > 35 else 'Low'} risk",
                  delta_color="inverse")

    # ── Gauges ──────────────────────────────────────────
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.plotly_chart(score_gauge(scores.get("demand_score", 0),
                        "Demand", "#3fb950"), use_container_width=True)
    with g2:
        st.plotly_chart(score_gauge(scores.get("pain_validation", 0),
                        "Pain", "#f85149"), use_container_width=True)
    with g3:
        st.plotly_chart(score_gauge(scores.get("competition_risk", 0),
                        "Competition", "#d29922"), use_container_width=True)
    with g4:
        st.plotly_chart(score_gauge(scores.get(
            "overall_failure_probability", 0), "Failure %", "#f47067"), use_container_width=True)

    # ── Tabs for different views ────────────────────────
    tab_report, tab_threads, tab_charts, tab_queries, tab_raw = st.tabs([
        "📝 Report", "🧵 Signal Threads", "📊 Charts", "🔍 Queries", "🗃️ Raw Data"
    ])

    # ── TAB: Report ─────────────────────────────────────
    with tab_report:
        st.markdown(report)

    # ── TAB: Signal Threads ─────────────────────────────
    with tab_threads:
        st.markdown(f'<div class="section-header">🧵 {len(threads)} Signal Threads Found</div>',
                    unsafe_allow_html=True)

        # Filters
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            signal_types = sorted(set(t.get("signal_type", "")
                                  for t in threads))
            filter_type = st.multiselect(
                "Filter by Signal Type", signal_types, default=signal_types)
        with fc2:
            min_relevance = st.slider("Min Relevance Score", 0, 100, 0)
        with fc3:
            sort_by = st.selectbox(
                "Sort By", ["Relevance", "Reddit Score", "Comments"])

        # Apply filters
        filtered = [
            t for t in threads
            if t.get("signal_type", "") in filter_type
            and t.get("relevance_score", 0) >= min_relevance
        ]

        # Sort
        if sort_by == "Relevance":
            filtered.sort(key=lambda t: t.get(
                "relevance_score", 0), reverse=True)
        elif sort_by == "Reddit Score":
            filtered.sort(key=lambda t: t.get("score", 0), reverse=True)
        elif sort_by == "Comments":
            filtered.sort(key=lambda t: t.get("num_comments", 0), reverse=True)

        st.caption(f"Showing {len(filtered)} of {len(threads)} threads")

        for i, thread in enumerate(filtered):
            render_thread_card(thread, i)

    # ── TAB: Charts ─────────────────────────────────────
    with tab_charts:
        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown(
                '<div class="section-header">📡 Signal Coverage</div>', unsafe_allow_html=True)
            st.plotly_chart(coverage_chart(coverage), use_container_width=True)
        with ch2:
            st.markdown(
                '<div class="section-header">🧩 Signal Distribution</div>', unsafe_allow_html=True)
            st.plotly_chart(signal_distribution_chart(
                threads), use_container_width=True)

        st.markdown(
            '<div class="section-header">🏘️ Subreddit Distribution</div>', unsafe_allow_html=True)
        st.plotly_chart(subreddit_chart(threads), use_container_width=True)

        # Relevance heatmap
        if threads:
            st.markdown(
                '<div class="section-header">🎯 Relevance vs Reddit Score</div>', unsafe_allow_html=True)
            df = pd.DataFrame(threads)
            if "relevance_score" in df.columns and "score" in df.columns:
                fig = px.scatter(
                    df,
                    x="score",
                    y="relevance_score",
                    size="num_comments",
                    color="signal_type",
                    hover_data=["title", "subreddit"],
                    color_discrete_map={
                        "pain_point": "#f85149",
                        "demand": "#3fb950",
                        "competition": "#d29922",
                        "skepticism": "#58a6ff",
                    },
                    labels={"score": "Reddit Score",
                            "relevance_score": "Relevance Score"},
                )
                fig.update_layout(
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="#21262d", tickfont={
                               "color": "#8b949e"}),
                    yaxis=dict(gridcolor="#21262d", tickfont={
                               "color": "#8b949e"}),
                    legend=dict(font=dict(color="#c9d1d9")),
                    font=dict(color="#f0f6fc"),
                )
                st.plotly_chart(fig, use_container_width=True)

        # Competitors table
        competitors_list = coverage.get("competitors", [])
        if competitors_list:
            st.markdown(
                '<div class="section-header">⚔️ Competitors Mentioned</div>', unsafe_allow_html=True)
            comp_cols = st.columns(min(len(competitors_list), 6))
            for i, comp in enumerate(competitors_list):
                with comp_cols[i % len(comp_cols)]:
                    st.markdown(
                        f'<div style="background:#21262d;border-radius:8px;padding:8px 14px;text-align:center;'
                        f'color:#d29922;font-weight:600;margin-bottom:6px;">{comp}</div>',
                        unsafe_allow_html=True,
                    )

    # ── TAB: Queries ────────────────────────────────────
    with tab_queries:
        st.markdown(f'<div class="section-header">🔍 {len(queries_used)} Search Queries Used</div>',
                    unsafe_allow_html=True)

        for i, q in enumerate(queries_used, 1):
            st.markdown(
                f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;'
                f'padding:10px 16px;margin-bottom:6px;color:#c9d1d9;">'
                f'<span style="color:#58a6ff;font-weight:700;">#{i}</span> &nbsp; {q}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("")
        st.markdown(
            f"**Iterations:** {iterations} &nbsp;|&nbsp; **Elapsed:** {elapsed:.1f}s &nbsp;|&nbsp; **Threads found:** {len(threads)}")

    # ── TAB: Raw Data ───────────────────────────────────
    with tab_raw:
        st.markdown(
            '<div class="section-header">🗃️ Raw Analysis Data</div>', unsafe_allow_html=True)

        # Export as CSV
        if threads:
            df = pd.DataFrame(threads)
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download Threads as CSV",
                csv,
                file_name="premortem_threads.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with st.expander("Full JSON Response", expanded=False):
            st.json(result)

        with st.expander("Scores", expanded=False):
            st.json(scores)

        with st.expander("Coverage", expanded=False):
            st.json(coverage)

        with st.expander(f"All Threads ({len(threads)})", expanded=False):
            st.json(threads)
