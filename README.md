# Prune

# **External Market Risk Engine for Startup Ideas**

PreMortem analyzes startup ideas using real external market signals before founders invest time and capital.

Instead of relying on optimism or vague AI opinions, PreMortem gathers live data from:

* GitHub (competition density)
* Web search results (market saturation)
* Reddit & forums (organic demand signals)

It then computes an evidence‑based failure probability using deterministic scoring logic.

---

## 🧠 Why PreMortem Exists

Startups don’t fail because founders lack intelligence.

They fail because:

* Demand was assumed, not validated
* Competition was underestimated
* Market saturation was ignored
* Optimism replaced evidence

PreMortem provides an external reality check at Day Zero.

---

# ⚙️ How It Works

## System Flow

flowchart TD
    A[Startup Idea Input] --> B[Keyword Extraction]
    B --> C[GitHub Search]
    B --> D[Web Search]
    B --> E[Reddit Signal Search]
    C --> F[Signal Aggregation]
    D --> F
    E --> F
    F --> G[Deterministic Risk Scoring]
    G --> H[Failure Probability Output]

---

# 🏗 Architecture

## Frontend

* Next.js (App Router)
* TailwindCSS
* Recharts (risk visualization)
* Mermaid.js (flowchart rendering)

## Backend

* Next.js API routes

## External APIs

* OpenAI API (keyword extraction only)
* Bing Web Search API (market signals)
* GitHub REST Search API (competition signals)

No database.
No authentication.
No persistent storage.

---

# 🔍 Core Features (MVP)

## 1️⃣ Idea Input

* Textarea for startup concept
* “Run PreMortem” button

---

## 2️⃣ Keyword Extraction (AI-Assisted)

OpenAI extracts:

* Main problem
* Target market
* Core keywords

AI does **not** score the idea.

---

## 3️⃣ External Signal Collection

### GitHub Search

Measures:

* Repository count
* Similar tools

Purpose:
Competition density indicator.

---

### Web Search (Bing API)

Measures:

* Market saturation
* Existing companies
* Product mentions

Purpose:
Market maturity signal.

---

### Reddit / Forum Signals

Measures:

* Complaint threads
* Pain discussions
* Organic demand signals

Purpose:
Real-world unmet need indicator.

---

# 📊 Scoring Model

PreMortem uses deterministic logic derived from real counts.

No hallucinated AI scores.

## Risk Dimensions

### Competition Risk

Based on GitHub repository count.

### Market Saturation Risk

Based on number of existing products in search results.

### Demand Strength

Based on number of Reddit/forum pain discussions.

### Execution Complexity Risk

Triggered by keywords like:

* AI
* Hardware
* Blockchain
* Infrastructure-heavy systems

---

## Final Failure Probability

Example deterministic formula:

<pre class="overflow-visible! px-0!" data-start="2888" data-end="3067"><div class="relative w-full my-4"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span>final_failure_probability =</span><br/><span>  (0.4 × competition_risk)</span><br/><span>+ (0.3 × market_saturation_risk)</span><br/><span>+ (0.2 × execution_complexity_risk)</span><br/><span>- (0.3 × demand_strength)</span><br/><br/><span>Normalized to 0–100.</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Higher demand reduces risk.
Higher competition increases risk.

---

# 📈 UI & Visualization

## Dashboard Layout

* Dark theme
* Clean card-based sections
* Centered analytics container

---

## Visual Components

### 🔴 Failure Probability

Large headline number with color logic:

* 0–40 → Green
* 40–70 → Yellow
* 70+ → Red

---

### 📊 Risk Breakdown Chart

Bar chart displaying:

* Competition Risk
* Market Saturation Risk
* Demand Strength
* Execution Complexity Risk

Built using Recharts.

---

### 📦 Signal Summary Cards

Displays:

* GitHub Repo Count
* Web Result Count
* Reddit Signal Count

Each with large numeric emphasis.

---

### 🔁 System Flow Visualization

Rendered with Mermaid.js to illustrate how the engine works.

---

# 🖥 Local Setup

## 1️⃣ Clone Repository

<pre class="overflow-visible! px-0!" data-start="3861" data-end="3911"><div class="relative w-full my-4"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span class="ͼ10">git</span><span> clone <your-repo-url></span><br/><span class="ͼ10">cd</span><span> premortem</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## 2️⃣ Install Dependencies

<pre class="overflow-visible! px-0!" data-start="3947" data-end="3970"><div class="relative w-full my-4"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span class="ͼ10">npm</span><span> install</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

If not already included:

<pre class="overflow-visible! px-0!" data-start="3998" data-end="4038"><div class="relative w-full my-4"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span class="ͼ10">npm</span><span> install recharts mermaid</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## 3️⃣ Environment Variables

Create `.env.local`

<pre class="overflow-visible! px-0!" data-start="4096" data-end="4188"><div class="relative w-full my-4"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span>OPENAI_API_KEY=your_key_here</span><br/><span>BING_API_KEY=your_key_here</span><br/><span>GITHUB_TOKEN=your_token_here</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## 4️⃣ Run Development Server

<pre class="overflow-visible! px-0!" data-start="4226" data-end="4249"><div class="relative w-full my-4"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span class="ͼ10">npm</span><span> run dev</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Open:

<pre class="overflow-visible! px-0!" data-start="4257" data-end="4286"><div class="relative w-full my-4"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span>http://localhost:3000</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 🎥 Demo Narrative

1. Paste weak idea.
2. Show:
   * High GitHub competition
   * Low Reddit demand
3. Reveal high failure probability.

Then paste strong niche idea:

* Lower competition
* Clear pain threads
* Lower failure probability.

Demonstrate contrast through evidence.

---

# 🚫 Non-Goals (MVP)

* No historical tracking
* No portfolio dashboard
* No defense mode
* No user accounts
* No predictive ML training
* No scraping private incubator data

This is a Day-Zero external signal engine.

---

# 🔮 Future Roadmap

* Idea history tracking
* Drift detection
* Founder commitment mode
* Portfolio analysis for VCs
* Trend evolution tracking
* Market heatmaps

---

# 🎯 Design Principles

* Evidence > Opinion
* Structure > Chat
* Deterministic logic > AI hallucination
* Clean analytics UI > Chat bubbles

PreMortem is not an idea validator.
It is an external market reality mirror.

---

If you'd like, I can now:

* Tighten this into a 1-page investor-ready product brief
* Or refine the scoring math to be more defensible and less arbitrary
* Or rewrite this README in a sharper YC-style tone
