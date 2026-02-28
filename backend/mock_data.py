"""
Mock data for testing the PreMortem Reddit Signal Engine.
Provides realistic sample inputs and outputs without hitting OpenAI or Reddit.
"""

# ─────────────────────────────────────────────────────────
# Sample startup inputs for testing
# ─────────────────────────────────────────────────────────
SAMPLE_INPUTS = [
    {
        "idea": "AI-powered resume screener for small businesses",
        "problem": "Small businesses waste 20+ hours per hire manually reading resumes and often miss great candidates",
        "solution": "An AI tool that auto-screens resumes, ranks candidates, and highlights red/green flags in seconds",
        "product_specs": "Web app, integrates with Gmail and job boards, uses GPT-4 for analysis, $49/month per seat",
    },
    {
        "idea": "Subscription fatigue manager — track and cancel unused subscriptions",
        "problem": "Average person pays for 12+ subscriptions and forgets about half of them, wasting $200+/month",
        "solution": "Connect your bank, auto-detect subscriptions, show usage stats, and one-click cancel unused ones",
        "product_specs": "Mobile app (iOS + Android), Plaid integration, freemium model, $4.99/month premium",
    },
    {
        "idea": "Local freelancer marketplace for home repairs",
        "problem": "Finding reliable handymen and freelancers for small home repairs is painful — Angi/Thumbtack are bloated and expensive",
        "solution": "Hyperlocal marketplace with verified freelancers, transparent pricing, and instant booking",
        "product_specs": "Mobile-first web app, Stripe payments, background checks, launch in 3 cities",
    },
    {
        "idea": "AI meeting summarizer that writes follow-up emails",
        "problem": "After every meeting people waste 15-30 minutes writing notes and follow-up emails, and most action items get lost",
        "solution": "Record meetings, auto-generate structured summaries with action items, and draft follow-up emails per attendee",
        "product_specs": "Chrome extension + Zoom/Meet plugin, GPT-4 for summarization, $12/month per user, SOC2 compliant",
    },
    {
        "idea": "Pet health monitoring wearable",
        "problem": "Pet owners can't tell when their dog or cat is sick until it's too late — vet visits are expensive and reactive",
        "solution": "Lightweight collar sensor that tracks vitals (heart rate, activity, sleep) and alerts owners to anomalies early",
        "product_specs": "BLE collar device + mobile app, $79 hardware + $9.99/month, integrates with vet clinics, dog-first then cats",
    },
    {
        "idea": "Micro-SaaS for restaurant menu A/B testing",
        "problem": "Restaurants guess at menu pricing and item placement — no data-driven way to optimize the menu for revenue",
        "solution": "Digital menu tool that lets restaurants A/B test item names, descriptions, prices, and placement with real diner data",
        "product_specs": "QR-code digital menu, analytics dashboard, Stripe integration, $29/month per location",
    },
    {
        "idea": "Creator-first invoicing and contract tool",
        "problem": "Freelance creators (designers, writers, videographers) waste hours on invoicing, contracts, and chasing payments",
        "solution": "All-in-one tool: send branded invoices, auto-generate contracts from templates, and get paid via Stripe with auto-reminders",
        "product_specs": "Web + mobile, Stripe Connect for payments, template library, $15/month, integrates with Notion and Figma",
    },
    {
        "idea": "Neighborhood safety alert app",
        "problem": "People don't know about crime or safety issues in their neighborhood until it's too late — Nextdoor is noisy and unstructured",
        "solution": "Hyper-local safety feed with verified incident reports, real-time alerts, and a safety score for every block",
        "product_specs": "Mobile app, uses public crime data APIs + user reports, free with premium alerts at $3.99/month, geofencing",
    },
    {
        "idea": "AI personal finance coach for Gen Z",
        "problem": "Gen Z earns money but has no idea how to budget, save, or invest — existing finance apps are boring and intimidating",
        "solution": "AI chatbot coach that speaks Gen Z language, gamifies saving, and gives personalized micro-lessons based on spending",
        "product_specs": "Mobile app, Plaid for bank linking, gamification with streaks and badges, freemium, $6.99/month premium",
    },
    {
        "idea": "Remote team virtual water cooler",
        "problem": "Remote teams lose spontaneous bonding — Slack is too async, Zoom is too formal, and culture erodes over time",
        "solution": "Always-on virtual lounge with drop-in audio rooms, random coffee pairing, and icebreaker games",
        "product_specs": "Web app + Slack bot, WebRTC for audio, $4/user/month, integrates with Google Calendar for auto-scheduling",
    },
]

# ─────────────────────────────────────────────────────────
# Mock analyzed threads (as if returned by the engine)
# ─────────────────────────────────────────────────────────
MOCK_THREADS = [
    {
        "thread_id": "abc123",
        "title": "We spent 40 hours last month just reading resumes for ONE junior dev role",
        "url": "https://reddit.com/r/smallbusiness/comments/abc123",
        "subreddit": "r/smallbusiness",
        "score": 342,
        "num_comments": 87,
        "relevance_score": 95,
        "signal_type": "pain_point",
        "insight": "Strong pain validation — small business owner describes exact problem of manual resume screening taking 40+ hours. Multiple commenters agree and share similar frustrations.",
        "competing_products": ["Lever", "Greenhouse", "JazzHR"],
        "unmet_needs": ["Affordable option for <10 employees", "No enterprise sales process"],
        "key_quotes": ["I literally spent my entire weekend reading 200 resumes for a $50k role. There has to be a better way."],
        "source_query": "small business hiring resume screening painful",
    },
    {
        "thread_id": "def456",
        "title": "Has anyone tried AI resume screening tools? Are they actually good?",
        "url": "https://reddit.com/r/recruiting/comments/def456",
        "subreddit": "r/recruiting",
        "score": 128,
        "num_comments": 45,
        "relevance_score": 88,
        "signal_type": "demand",
        "insight": "Direct demand signal — user is actively searching for AI resume screening. Commenters recommend several tools but note they're all 'enterprise-priced' and overkill for small teams.",
        "competing_products": ["HireVue", "Pymetrics", "Ideal"],
        "unmet_needs": ["Simple setup without IT team", "Pay-per-use pricing"],
        "key_quotes": ["I just need something that filters out the obvious non-fits. I don't need a $500/month enterprise platform."],
        "source_query": "AI resume screening tool recommendation",
    },
    {
        "thread_id": "ghi789",
        "title": "Why I stopped using Lever for our 5-person startup",
        "url": "https://reddit.com/r/startups/comments/ghi789",
        "subreddit": "r/startups",
        "score": 256,
        "num_comments": 63,
        "relevance_score": 82,
        "signal_type": "competition",
        "insight": "Competitive intelligence — founder switched away from Lever citing cost ($300/month) and complexity. Looking for simpler alternatives. Thread reveals pricing dissatisfaction across multiple ATS tools.",
        "competing_products": ["Lever", "Workable", "Breezy HR"],
        "unmet_needs": ["Transparent pricing", "Quick onboarding", "AI built-in not bolt-on"],
        "key_quotes": ["Lever wanted $300/month for 3 users. We're a 5-person startup hiring maybe 2 people a quarter. The math doesn't work."],
        "source_query": "startup hiring tool too expensive alternative",
    },
    {
        "thread_id": "jkl012",
        "title": "AI hiring tools are just automated bias machines — change my mind",
        "url": "https://reddit.com/r/cscareerquestions/comments/jkl012",
        "subreddit": "r/cscareerquestions",
        "score": 891,
        "num_comments": 234,
        "relevance_score": 76,
        "signal_type": "skepticism",
        "insight": "Significant skepticism about AI bias in hiring. Multiple commenters share stories of being filtered out by ATS systems. Any AI resume tool must address bias concerns head-on.",
        "competing_products": ["HireVue", "Amazon's scrapped AI recruiter"],
        "unmet_needs": ["Bias auditing / transparency", "Human-in-the-loop design"],
        "key_quotes": ["Amazon literally had to scrap their AI hiring tool because it was biased against women. Why would a small startup's version be any better?"],
        "source_query": "AI resume screening bias problems",
    },
    {
        "thread_id": "mno345",
        "title": "Best free/cheap ATS for bootstrapped startup?",
        "url": "https://reddit.com/r/EntrepreneurRideAlong/comments/mno345",
        "subreddit": "r/EntrepreneurRideAlong",
        "score": 167,
        "num_comments": 52,
        "relevance_score": 71,
        "signal_type": "demand",
        "insight": "Budget-conscious founders actively seeking affordable hiring tools. Top recommendations are all basic ATS without AI features — clear gap in the market.",
        "competing_products": ["Notion job board template", "Google Forms", "Airtable"],
        "unmet_needs": ["Free tier for first 5 hires", "AI screening at low cost"],
        "key_quotes": ["We just use a shared Google Sheet to track candidates. It's terrible but everything else costs too much."],
        "source_query": "cheap hiring tool bootstrapped startup",
    },
    {
        "thread_id": "pqr678",
        "title": "How do you handle 500+ applications for a single remote role?",
        "url": "https://reddit.com/r/remotework/comments/pqr678",
        "subreddit": "r/remotework",
        "score": 445,
        "num_comments": 112,
        "relevance_score": 68,
        "signal_type": "pain_point",
        "insight": "Remote work has massively increased application volume. Hiring managers describe being overwhelmed. This validates the core problem — volume is only growing.",
        "competing_products": [],
        "unmet_needs": ["Batch processing for high-volume roles", "Quick reject with auto-email"],
        "key_quotes": ["Posted a remote customer support role and got 800 applications in 48 hours. I wanted to cry."],
        "source_query": "too many job applications overwhelmed hiring",
    },
]

# ─────────────────────────────────────────────────────────
# Mock scores
# ─────────────────────────────────────────────────────────
MOCK_SCORES = {
    "demand_score": 78,
    "competition_risk": 65,
    "pain_validation": 88,
    "overall_failure_probability": 35,
}

# ─────────────────────────────────────────────────────────
# Mock coverage
# ─────────────────────────────────────────────────────────
MOCK_COVERAGE = {
    "counts": {
        "pain_point": 2,
        "competition": 1,
        "demand": 2,
        "skepticism": 1,
    },
    "competitors": ["Lever", "Greenhouse", "JazzHR", "HireVue", "Pymetrics", "Ideal", "Workable", "Breezy HR"],
    "gaps": [],
    "has_gaps": False,
}

# ─────────────────────────────────────────────────────────
# Mock report (markdown)
# ─────────────────────────────────────────────────────────
MOCK_REPORT = """\
# PreMortem Market Signal Report: AI Resume Screener for Small Businesses

## 1. Executive Summary

Strong demand signals with validated pain points. Small businesses are genuinely struggling with resume volume and existing tools are priced for enterprise. Competition exists but is poorly positioned for the SMB segment. **Overall: Promising idea with a clear wedge — affordability + simplicity.**

## 2. Demand Signals

**Score: 78/100 — Strong demand detected**

Multiple Reddit threads show founders and small business owners actively searching for affordable AI hiring tools:

- **r/EntrepreneurRideAlong** — Bootstrapped founders using Google Sheets and Notion to track candidates because every ATS is "too expensive" ([thread](https://reddit.com/r/EntrepreneurRideAlong/comments/mno345))
- **r/recruiting** — Recruiter explicitly asking for AI resume screening that isn't enterprise-priced: *"I just need something that filters out the obvious non-fits"* ([thread](https://reddit.com/r/recruiting/comments/def456))

## 3. Competition Landscape

**Risk: 65/100 — Moderate competition, but poorly targeted at SMB**

Key competitors identified:
| Product | Pricing | SMB Fit |
|---------|---------|---------|
| Lever | $300+/mo | ❌ Enterprise |
| Greenhouse | $400+/mo | ❌ Enterprise |
| JazzHR | $49/mo | ⚠️ Basic ATS, no AI |
| HireVue | Enterprise | ❌ Video-focused |
| Workable | $149/mo | ⚠️ Decent but pricey |

**Key insight:** No competitor offers AI-powered screening at the $49/month price point for small teams. The gap is real.

## 4. Pain Points Validated

**Score: 88/100 — Very strong validation**

- A small business owner spent **40+ hours reading 200 resumes** for a single role ([thread](https://reddit.com/r/smallbusiness/comments/abc123))
- A remote job posting received **800 applications in 48 hours**, overwhelming the hiring manager ([thread](https://reddit.com/r/remotework/comments/pqr678))
- Multiple founders describe the resume screening process as their **least favorite part of running a business**

## 5. Red Flags & Skepticism

**⚠️ AI bias is a real concern**

A highly-upvoted thread (891 upvotes) on r/cscareerquestions raises serious concerns about AI bias in hiring, citing Amazon's failed AI recruiter. Key quote: *"Amazon literally had to scrap their AI hiring tool because it was biased against women."* ([thread](https://reddit.com/r/cscareerquestions/comments/jkl012))

**Mitigation needed:** Transparent scoring, bias auditing, and human-in-the-loop design are essential.

## 6. Unmet Needs & Opportunities

1. **Affordable AI screening** — No one offers AI at <$50/month
2. **No-IT-team setup** — Small businesses don't have HR tech teams
3. **Free tier for first hires** — Founders want to try before committing
4. **Bias transparency** — Show why candidates were ranked, not just scores
5. **Pay-per-use option** — Seasonal hirers don't want monthly subscriptions

## 7. Recommendation

### ✅ GO — with conditions

**Reasoning:** The pain is validated (88/100), demand is strong (78/100), and competition is poorly positioned for SMB. The $49/month price point has no AI-powered competitor.

**Conditions:**
1. Build bias auditing from day one — this is a PR landmine if ignored
2. Offer a generous free tier to win bootstrapped founders
3. Integrate with Gmail/Google Workspace — that's where small businesses live
4. Avoid the word "AI" in marketing to skeptical buyers; focus on "save 20 hours per hire"

**Estimated failure probability: 35%** — mostly driven by execution risk and the bias perception challenge.
"""

# ─────────────────────────────────────────────────────────
# Full mock engine response (combines all above)
# ─────────────────────────────────────────────────────────
MOCK_ENGINE_RESULT = {
    "report": MOCK_REPORT,
    "scores": MOCK_SCORES,
    "threads": MOCK_THREADS,
    "iterations": 2,
    "queries_used": [
        "small business hiring resume screening painful",
        "AI resume screening tool recommendation",
        "startup hiring tool too expensive alternative",
        "AI resume screening bias problems",
        "cheap hiring tool bootstrapped startup",
        "too many job applications overwhelmed hiring",
    ],
    "coverage": MOCK_COVERAGE,
    "elapsed_seconds": 42.3,
}

# ─────────────────────────────────────────────────────────
# Mock generated queries (Stage 1 output)
# ─────────────────────────────────────────────────────────
MOCK_GENERATED_QUERIES = [
    {
        "query": "small business hiring resume screening painful",
        "intent": "pain_point",
        "subreddits": ["r/smallbusiness", "r/Entrepreneur"],
    },
    {
        "query": "AI resume screening tool recommendation",
        "intent": "demand",
        "subreddits": ["r/recruiting", "r/humanresources"],
    },
    {
        "query": "startup hiring tool too expensive alternative",
        "intent": "competition",
        "subreddits": ["r/startups", "r/SaaS"],
    },
    {
        "query": "AI resume screening bias problems",
        "intent": "skepticism",
        "subreddits": ["r/cscareerquestions", "r/MachineLearning"],
    },
    {
        "query": "cheap hiring tool bootstrapped startup",
        "intent": "demand",
        "subreddits": ["r/EntrepreneurRideAlong", "r/startups"],
    },
    {
        "query": "too many job applications overwhelmed hiring",
        "intent": "pain_point",
        "subreddits": ["r/remotework", "r/jobs"],
    },
]

# ─────────────────────────────────────────────────────────
# Mock Reddit search results (raw threads before analysis)
# ─────────────────────────────────────────────────────────
MOCK_RAW_REDDIT_THREADS = [
    {
        "id": "abc123",
        "title": "We spent 40 hours last month just reading resumes for ONE junior dev role",
        "selftext": "I run a 12-person agency. We posted a junior developer role and got 200+ applications. My co-founder and I split them up and it still took us 40 hours total to go through them all. Most were completely unqualified. There has to be a better way to do this. What do other small businesses use?",
        "subreddit": "r/smallbusiness",
        "score": 342,
        "num_comments": 87,
        "url": "https://reddit.com/r/smallbusiness/comments/abc123",
        "created_utc": 1700000000,
        "upvote_ratio": 0.94,
        "source_query": "small business hiring resume screening painful",
        "top_comments": [
            "Same here. We use JazzHR but it doesn't help with actually screening, just organizing.",
            "Have you looked into AI tools? I heard Lever has some AI features but it's like $300/month.",
            "We just started using a Google Form as a pre-screen. Cuts out 50% of junk applications.",
        ],
    },
    {
        "id": "def456",
        "title": "Has anyone tried AI resume screening tools? Are they actually good?",
        "selftext": "I'm a recruiter at a 30-person company. We're getting 100+ applications per role and I can't keep up. Has anyone used an AI tool to screen resumes? Looking for something affordable, not enterprise.",
        "subreddit": "r/recruiting",
        "score": 128,
        "num_comments": 45,
        "url": "https://reddit.com/r/recruiting/comments/def456",
        "created_utc": 1701000000,
        "upvote_ratio": 0.91,
        "source_query": "AI resume screening tool recommendation",
        "top_comments": [
            "I tried HireVue but it's way too expensive and focused on video interviews.",
            "Pymetrics is interesting but it's more about assessments than resume screening.",
            "I just need something that filters out the obvious non-fits. I don't need a $500/month enterprise platform.",
        ],
    },
]
