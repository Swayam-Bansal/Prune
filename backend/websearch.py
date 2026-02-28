
import os
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


class WebSearchError(RuntimeError):
    pass


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


def _clean_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _tokenize(s: str) -> List[str]:
    s = (s or "").lower()
    return re.findall(r"[a-z0-9]+", s)


def _lexical_similarity(a: str, b: str) -> float:
    ta = set(_tokenize(a))
    tb = set(_tokenize(b))
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return float(inter) / float(union) if union else 0.0


def _clamp01(x: Any) -> float:
    try:
        v = float(x)
    except Exception:
        return 0.0
    if v < 0:
        return 0.0
    if v > 1:
        return 1.0
    return v


def _is_probably_company_domain(domain: str) -> bool:
    if not domain:
        return False
    domain = domain.lower().strip(".")
    if domain.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        return False
    blocked = (
        "wikipedia.org",
        "linkedin.com",
        "facebook.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "youtube.com",
        "crunchbase.com",
        "pitchbook.com",
        "tracxn.com",
        "g2.com",
        "capterra.com",
        "ycombinator.com",
        "github.com",
        "medium.com",
        "substack.com",
        "reddit.com",
        "producthunt.com",
    )
    return not any(domain == b or domain.endswith("." + b) for b in blocked)


def _get_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse

        host = urlparse(url).netloc
        host = host.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _http_get(url: str, timeout_s: int = 12) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=timeout_s)
    resp.raise_for_status()
    return resp.text


def _extract_page_text(html: str, max_chars: int = 12000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = _clean_whitespace(soup.title.get_text(" ") if soup.title else "")
    meta_desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta_desc = _clean_whitespace(md.get("content"))

    chunks: List[str] = []
    if title:
        chunks.append(f"Title: {title}")
    if meta_desc:
        chunks.append(f"Description: {meta_desc}")

    text = _clean_whitespace(soup.get_text(" "))
    if text:
        chunks.append(text)

    joined = _clean_whitespace("\n".join(chunks))
    if len(joined) > max_chars:
        joined = joined[:max_chars]
    return joined


def _duckduckgo_search(query: str, max_results: int = 10) -> List[SearchResult]:
    try:
        from duckduckgo_search import DDGS
    except Exception as e:
        raise WebSearchError(
            "duckduckgo_search dependency not installed (or not available in the current Python environment). "
            "Install with: python -m pip install -r requirements.txt. "
            f"Underlying error: {e}"
        ) from e

    last_err: Optional[Exception] = None
    for attempt in range(4):
        try:
            results: List[SearchResult] = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    title = _clean_whitespace(r.get("title", ""))
                    url = _clean_whitespace(r.get("href", ""))
                    snippet = _clean_whitespace(r.get("body", ""))
                    if not url:
                        continue
                    results.append(SearchResult(title=title, url=url, snippet=snippet))
            return results
        except Exception as e:
            last_err = e
            msg = str(e)
            is_rate_limited = ("ratelimit" in msg.lower()) or ("202" in msg)
            if not is_rate_limited or attempt == 3:
                break
            time.sleep(1.0 * (2**attempt))

    raise WebSearchError(
        "DuckDuckGo search failed (likely rate limited). Try again in ~30-120s, "
        "or reduce max_companies/max_pages_per_company. "
        f"Underlying error: {last_err}"
    )


def _gemini_summarize(prompt: str, model: str = "gemini-1.5-flash") -> Optional[str]:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        import google.generativeai as genai
    except Exception as e:
        raise WebSearchError(
            "Gemini SDK not available. Install dependencies with: python -m pip install -r requirements.txt. "
            f"Underlying error: {e}"
        ) from e

    genai.configure(api_key=api_key)

    env_model = os.getenv("GEMINI_MODEL")
    preferred = [
        env_model,
        model,
        "models/gemini-flash-latest",
        "models/gemini-pro-latest",
        "models/gemini-2.0-flash",
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro",
    ]
    preferred = [m for m in preferred if isinstance(m, str) and m.strip()]

    def _normalize(mname: str) -> str:
        mname = mname.strip()
        return mname if mname.startswith("models/") else f"models/{mname}"

    preferred = [_normalize(m) for m in preferred]

    last_err: Optional[Exception] = None
    tried: List[str] = []
    for mname in preferred:
        try:
            tried.append(mname)
            m = genai.GenerativeModel(mname)
            resp = m.generate_content(
                prompt,
                generation_config={"temperature": 0.2},
            )
            text = getattr(resp, "text", None)
            return text.strip() if isinstance(text, str) and text.strip() else None
        except Exception as e:
            last_err = e
            continue

    available: List[str] = []
    try:
        for mdl in genai.list_models():
            name = getattr(mdl, "name", None)
            supported = getattr(mdl, "supported_generation_methods", None)
            if isinstance(name, str) and name:
                if not supported or ("generateContent" in supported):
                    available.append(name)
        available = available[:30]
    except Exception:
        available = []

    if available:
        for mname in available:
            if mname in tried:
                continue
            try:
                m = genai.GenerativeModel(mname)
                resp = m.generate_content(
                    prompt,
                    generation_config={"temperature": 0.2},
                )
                text = getattr(resp, "text", None)
                return text.strip() if isinstance(text, str) and text.strip() else None
            except Exception as e:
                last_err = e
                continue

    extra = f" Available models: {available}" if available else ""
    raise WebSearchError(
        "Gemini request failed (check API key validity, quota/billing, and model name). "
        f"Underlying error: {last_err}.{extra}"
    )

    


def _has_gemini_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def gemini_idea_research(
    idea: str,
    *,
    problem: str = "",
    solution: str = "",
    product_specs: str = "",
    max_companies: int = 6,
) -> Dict[str, Any]:
    idea = _clean_whitespace(idea)
    problem = _clean_whitespace(problem)
    solution = _clean_whitespace(solution)
    product_specs = _clean_whitespace(product_specs)
    if not idea:
        return {
            "idea": "",
            "problem": "",
            "solution": "",
            "product_specs": "",
            "companies": [],
            "deep_dives": [],
        }

    prompt = f"""You are doing market research.

The user is giving you 4 inputs: idea, problem, solution, product specs.

IMPORTANT:
- Do not browse the web.
- Use your general knowledge.
- If unsure about a specific company detail, say so.

Return ONLY valid JSON with this exact top-level schema:
{{
  "idea": string,
  "problem": string,
  "solution": string,
  "product_specs": string,
  "companies": [
    {{"name": string, "domain": string|null, "one_liner": string, "similarity_score": number, "similarity_reason": string}}
  ],
  "deep_dives": [
    {{
      "company": {{"name": string, "domain": string|null}},
      "similarity_score": number,
      "similarity_reason": string,
      "profile": {{
        "what_they_do": string,
        "target_customer": string,
        "key_features": [string],
        "unique_differentiators": [string],
        "business_model": string,
        "positioning_vs_idea": string,
        "notable_signals": [string]
      }}
    }}
  ]
}}

INPUTS:
idea: {idea}
problem: {problem}
solution: {solution}
product_specs: {product_specs}
max_companies: {max_companies}
"""

    text = _gemini_summarize(prompt)
    if not text:
        raise WebSearchError("Gemini API key not set. Set GEMINI_API_KEY or GOOGLE_API_KEY.")

    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Gemini returned non-object JSON")

        data.setdefault("idea", idea)
        data.setdefault("problem", problem)
        data.setdefault("solution", solution)
        data.setdefault("product_specs", product_specs)

        for c in data.get("companies", []) if isinstance(data.get("companies"), list) else []:
            if isinstance(c, dict):
                c["similarity_score"] = _clamp01(c.get("similarity_score"))
                if not c.get("similarity_reason"):
                    c["similarity_reason"] = ""

        for d in data.get("deep_dives", []) if isinstance(data.get("deep_dives"), list) else []:
            if isinstance(d, dict):
                d["similarity_score"] = _clamp01(d.get("similarity_score"))
                if not d.get("similarity_reason"):
                    d["similarity_reason"] = ""

        return data
    except Exception:
        return {
            "idea": idea,
            "problem": problem,
            "solution": solution,
            "product_specs": product_specs,
            "companies": [],
            "deep_dives": [],
            "raw": text,
        }


def find_similar_companies(
    idea: str,
    *,
    max_companies: int = 8,
    search_results_per_query: int = 10,
    sleep_s: float = 0.8,
) -> List[Dict[str, Any]]:
    idea = _clean_whitespace(idea)
    if not idea:
        return []

    queries = [
        f"{idea} startup",
        f"{idea} company",
        f"{idea} competitors",
        f"companies like {idea}",
        f"alternative to {idea}",
    ]

    by_domain: Dict[str, Dict[str, Any]] = {}
    for q in queries:
        time.sleep(sleep_s)
        for r in _duckduckgo_search(q, max_results=search_results_per_query):
            domain = _get_domain(r.url)
            if not _is_probably_company_domain(domain):
                continue
            if domain not in by_domain:
                by_domain[domain] = {
                    "domain": domain,
                    "name": r.title.split("|")[0].split("-")[0].strip() or domain,
                    "homepage": r.url,
                    "evidence": [{"query": q, "title": r.title, "url": r.url, "snippet": r.snippet}],
                }
            else:
                by_domain[domain]["evidence"].append(
                    {"query": q, "title": r.title, "url": r.url, "snippet": r.snippet}
                )
            if len(by_domain) >= max_companies:
                break
        if len(by_domain) >= max_companies:
            break

    return list(by_domain.values())[:max_companies]


def _company_research_queries(company: Dict[str, Any], idea: str) -> List[str]:
    name = company.get("name") or company.get("domain") or ""
    domain = company.get("domain") or ""
    base = []
    if domain:
        base.extend(
            [
                f"site:{domain} about",
                f"site:{domain} product",
                f"site:{domain} pricing",
                f"site:{domain} customers",
                f"site:{domain} case study",
            ]
        )
    base.extend(
        [
            f"{name} what does it do",
            f"{name} product features",
            f"{name} pricing",
            f"{name} competitors",
            f"{name} {idea}",
        ]
    )
    return base


def deep_dive_company(
    company: Dict[str, Any],
    idea: str,
    *,
    max_pages: int = 4,
    max_search_results: int = 8,
    sleep_s: float = 0.8,
) -> Dict[str, Any]:
    domain = company.get("domain")
    queries = _company_research_queries(company, idea)

    urls: List[str] = []
    sources: List[Dict[str, str]] = []
    for q in queries:
        time.sleep(sleep_s)
        for r in _duckduckgo_search(q, max_results=max_search_results):
            if len(urls) >= max_pages:
                break
            if domain and _get_domain(r.url) == domain:
                pass
            u = r.url
            if u in urls:
                continue
            urls.append(u)
            sources.append({"title": r.title, "url": r.url, "snippet": r.snippet})
        if len(urls) >= max_pages:
            break

    page_texts: List[Tuple[str, str]] = []
    for u in urls:
        try:
            html = _http_get(u)
            text = _extract_page_text(html)
            if text:
                page_texts.append((u, text))
        except Exception:
            continue

    joined = "\n\n".join([f"URL: {u}\n{text}" for (u, text) in page_texts])

    prompt = (
        "Given the idea and the sources, write a concise but in-depth company profile.\n\n"
        f"IDEA: {idea}\n\n"
        f"COMPANY: {company.get('name','')} ({company.get('domain','')})\n\n"
        "Return a JSON object with keys: what_they_do, target_customer, key_features, unique_differentiators, "
        "business_model, positioning_vs_idea, notable_signals.\n\n"
        "SOURCES TEXT (may be noisy):\n"
        f"{joined}\n"
    )

    summary = _gemini_summarize(prompt)

    return {
        "company": {"name": company.get("name"), "domain": company.get("domain"), "homepage": company.get("homepage")},
        "similarity_score": _clamp01(
            _lexical_similarity(idea, f"{company.get('name','')} {company.get('domain','')}")
        ),
        "similarity_reason": "",
        "sources": sources,
        "raw_text": joined if not summary else None,
        "profile": summary,
    }


def websearch_idea(
    idea: str,
    *,
    problem: str = "",
    solution: str = "",
    product_specs: str = "",
    max_companies: int = 6,
    max_pages_per_company: int = 4,
) -> Dict[str, Any]:
    if _has_gemini_key():
        return gemini_idea_research(
            idea,
            problem=problem,
            solution=solution,
            product_specs=product_specs,
            max_companies=max_companies,
        )

    companies = find_similar_companies(idea, max_companies=max_companies)
    deep_dives: List[Dict[str, Any]] = []
    for c in companies:
        deep_dives.append(deep_dive_company(c, idea, max_pages=max_pages_per_company))
    for c in companies:
        if isinstance(c, dict):
            evidence_text = " ".join(
                [
                    str(ev.get("title", "")) + " " + str(ev.get("snippet", ""))
                    for ev in (c.get("evidence") or [])
                    if isinstance(ev, dict)
                ]
            )
            c["similarity_score"] = _clamp01(_lexical_similarity(idea, evidence_text))
            c["similarity_reason"] = ""
    return {"idea": _clean_whitespace(idea), "companies": companies, "deep_dives": deep_dives}

