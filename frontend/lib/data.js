export const FAILURE = 72;

export const RISKS = [
  { name: "Competition",     value: 78 },
  { name: "Mkt Saturation",  value: 65 },
  { name: "Demand Strength", value: 54 },
  { name: "Exec Complexity", value: 71 },
];

export const SIGNALS = [
  { icon: "📂", num: 1243, label: "GitHub Repos Found",    color: "#c4b5fd" },
  { icon: "🌐", num: 8700, label: "Market Results Found",  color: "#7dd3fc" },
  { icon: "💬", num: 347,  label: "Reddit Demand Signals", color: "#fdba74" },
];

export const INSIGHTS = [
  "1,243 GitHub repos found — active OSS ecosystem exists; developer competition is significant in this space.",
  "8,700 web market results — meaningful existing presence; niche positioning and differentiation are critical.",
  "347 Reddit demand signals — moderate user pain vocalized online; demand is real but not yet urgent at scale.",
  "Moderate-to-high execution complexity detected — achievable with a capable team, but watch scope creep in early sprints.",
];

export const KEYWORDS = {
  main_problem:  "legal contract generation",
  target_market: "freelancers & small businesses",
  core_keywords: ["legal contracts", "freelance", "document automation"],
};

// ─── Similar Startups (Gemini search results) ─────────────────────────────────
export const SIMILAR_STARTUPS = [
  {
    name: "HelloSign",
    desc: "E-signature and contract workflow platform designed for freelancers and small businesses. Acquired by Dropbox.",
    url: "https://hellosign.com",
    stage: "Acquired",
    similarity: 91,
  },
  {
    name: "PandaDoc",
    desc: "Document automation SaaS — create, send, and e-sign proposals, quotes, and contracts in minutes.",
    url: "https://pandadoc.com",
    stage: "Series B",
    similarity: 86,
  },
  {
    name: "Ironclad",
    desc: "Digital contracting platform built for legal teams at scale. Automates the entire contract lifecycle.",
    url: "https://ironcladapp.com",
    stage: "Series D",
    similarity: 79,
  },
  {
    name: "Bonsai",
    desc: "All-in-one freelance business tool — contracts, proposals, invoicing, and time tracking in one flow.",
    url: "https://hellobonsai.com",
    stage: "Series A",
    similarity: 74,
  },
];

// ─── Reddit Threads (demand & pain point intelligence) ────────────────────────
export const REDDIT_THREADS = [
  {
    title: "Why are legal contracts so expensive for freelancers? Is there a cheaper way?",
    url: "#",
    subreddit: "r/freelance",
    upvotes: 847,
    comments: 193,
    similarity: 94,
    pain_points: [
      "Lawyer fees unaffordable for solo freelancers",
      "Generic templates miss jurisdiction-specific clauses",
      "Clients often reject informal contracts",
    ],
    competition_signal: "High",
  },
  {
    title: "Tools to auto-generate client contracts as a solo developer?",
    url: "#",
    subreddit: "r/webdev",
    upvotes: 612,
    comments: 88,
    similarity: 87,
    pain_points: [
      "Time-consuming to draft from scratch each time",
      "Existing templates are too generic",
      "No good SaaS option under $20/mo",
    ],
    competition_signal: "Moderate",
  },
  {
    title: "DocuSign alternatives that don't cost $50/month for one person?",
    url: "#",
    subreddit: "r/Entrepreneur",
    upvotes: 1204,
    comments: 267,
    similarity: 81,
    pain_points: [
      "Pricing too high for solopreneurs",
      "Feature bloat — most people need 10% of the features",
      "Onboarding is overly complex",
    ],
    competition_signal: "High",
  },
];

// ─── GitHub Repos (competition mapping) ──────────────────────────────────────
export const GITHUB_REPOS = [
  {
    name: "docassemble/docassemble",
    desc: "A free, open-source expert system for guided interviews and document assembly in legal aid workflows.",
    stars: 3200,
    language: "Python",
    url: "https://github.com/docassemble/docassemble",
  },
  {
    name: "ContractPatch/contracts",
    desc: "Open-source legal contract templates for developers and freelancers, covering NDAs, service agreements, and IP transfer.",
    stars: 891,
    language: "Markdown",
    url: "#",
  },
  {
    name: "legal-tech/document-gen",
    desc: "AI-powered document generation toolkit for legal professionals — integrates with OpenAI to draft clause-aware contracts.",
    stars: 445,
    language: "TypeScript",
    url: "#",
  },
  {
    name: "open-source/legal-helper",
    desc: "Lightweight CLI tool for generating NDAs and service agreements from YAML configuration files.",
    stars: 210,
    language: "Go",
    url: "#",
  },
];
