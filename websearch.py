"""
Web Search Module v1.0 — Connected
====================================
Uses keys.py for AI analysis of results.
Uses memory.py to cache search results.
Imported by: agent.py, chainlit_app.py, security_agent.py
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

# ── Import shared modules ─────────────────────────────────────
try:
    from keys import call_ai, call_fast, ONLINE_POOL
    from memory import save_research
    _modules_loaded = True
except ImportError:
    _modules_loaded = False
    def call_ai(m, *a, **k): return "AI unavailable", "none"
    def save_research(*a, **k): pass

# ══════════════════════════════════════════════════════════════
# DUCKDUCKGO — 100% Free, No Key
# ══════════════════════════════════════════════════════════════

def _get_ddgs_class():
    """duckduckgo_search was renamed to ddgs; support both package names."""
    try:
        from ddgs import DDGS
        return DDGS
    except ImportError:
        pass
    try:
        from duckduckgo_search import DDGS
        return DDGS
    except ImportError:
        import subprocess
        subprocess.run(
            "pip3 install ddgs --break-system-packages",
            shell=True, capture_output=True)
        from ddgs import DDGS
        return DDGS

def ddg_search(query: str, n: int = 5) -> list:
    """DuckDuckGo search — completely free, no API key."""
    try:
        DDGS = _get_ddgs_class()
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=n):
                results.append({
                    "title":   r.get("title", ""),
                    "url":     r.get("href", ""),
                    "snippet": r.get("body", "")[:300]
                })
        return results
    except Exception as e:
        return [{"error": str(e)}]

def ddg_news(query: str, n: int = 5) -> list:
    """DuckDuckGo news search."""
    try:
        DDGS = _get_ddgs_class()
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=n):
                results.append({
                    "title":   r.get("title", ""),
                    "url":     r.get("url", ""),
                    "snippet": r.get("body", "")[:300],
                    "date":    r.get("date", "")
                })
        return results
    except Exception as e:
        return [{"error": str(e)}]

# ══════════════════════════════════════════════════════════════
# TAVILY — Free Tier (AI-optimized)
# ══════════════════════════════════════════════════════════════

def tavily_search(query: str, n: int = 5) -> dict:
    """Tavily AI search — free tier 1000/month."""
    import os
    key = os.environ.get("TAVILY_API_KEY", "")
    if not key:
        return {"note": "No Tavily key — using DuckDuckGo",
                "results": ddg_search(query, n)}
    try:
        from tavily import TavilyClient
        return TavilyClient(api_key=key).search(
            query=query, max_results=n)
    except Exception as e:
        return {"error": str(e),
                "results": ddg_search(query, n)}

# ══════════════════════════════════════════════════════════════
# CVE SEARCH — NVD API (Free, No Auth)
# ══════════════════════════════════════════════════════════════

def search_cves(keyword: str,
                days_back: int = 180,
                min_score: float = 0.0) -> list:
    """Search NVD for CVEs — free, no auth needed."""
    end   = datetime.now()
    start = end - timedelta(days=days_back)
    url   = (
        "https://services.nvd.nist.gov/rest/json/cves/2.0"
        f"?keywordSearch={keyword}"
        f"&pubStartDate={start.strftime('%Y-%m-%dT00:00:00.000')}"
        f"&pubEndDate={end.strftime('%Y-%m-%dT23:59:59.000')}"
        f"&resultsPerPage=20"
    )
    try:
        r    = requests.get(url, timeout=15)
        cves = []
        for v in r.json().get("vulnerabilities", []):
            cve   = v.get("cve", {})
            score = (cve.get("metrics", {})
                    .get("cvssMetricV31", [{}])[0]
                    .get("cvssData", {})
                    .get("baseScore", 0))
            if float(score or 0) >= min_score:
                refs = [ref.get("url", "")
                        for ref in cve.get("references", [])[:3]]
                cves.append({
                    "id":    cve.get("id", ""),
                    "score": score,
                    "desc":  cve.get("descriptions",
                                     [{}])[0].get("value", "")[:250],
                    "refs":  refs
                })
        return sorted(cves,
                      key=lambda x: float(x.get("score") or 0),
                      reverse=True)
    except Exception as e:
        return [{"error": str(e)}]

def get_cve_details(cve_id: str) -> dict:
    """Get specific CVE details."""
    try:
        r = requests.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0"
            f"?cveId={cve_id}",
            timeout=10)
        vulns = r.json().get("vulnerabilities", [])
        if vulns:
            return vulns[0].get("cve", {})
        return {"error": "CVE not found"}
    except Exception as e:
        return {"error": str(e)}

# ══════════════════════════════════════════════════════════════
# ARXIV — Free, Unlimited
# ══════════════════════════════════════════════════════════════

def search_arxiv(query: str, n: int = 5) -> list:
    """Search ArXiv research papers — free, unlimited."""
    try:
        import arxiv
        search  = arxiv.Search(query=query, max_results=n,
            sort_by=arxiv.SortCriterion.Relevance)
        return [{
            "title":     r.title,
            "authors":   [str(a) for a in r.authors[:3]],
            "summary":   r.summary[:300],
            "url":       r.entry_id,
            "published": str(r.published)[:10]
        } for r in search.results()]
    except Exception as e:
        return [{"error": str(e)}]

# ══════════════════════════════════════════════════════════════
# WIKIPEDIA — Free, Unlimited
# ══════════════════════════════════════════════════════════════

def search_wikipedia(query: str) -> str:
    """Search Wikipedia — free, unlimited."""
    try:
        import wikipedia
        return wikipedia.summary(query, sentences=5)
    except Exception:
        try:
            import wikipedia
            results = wikipedia.search(query)
            if results:
                return wikipedia.summary(results[0], sentences=5)
        except Exception as e:
            return f"Wikipedia error: {e}"
    return "No results found"

# ══════════════════════════════════════════════════════════════
# EXPLOITDB — Via searchsploit
# ══════════════════════════════════════════════════════════════

def search_exploitdb(keyword: str) -> str:
    """Search ExploitDB via searchsploit."""
    import subprocess, shutil
    if not shutil.which("searchsploit"):
        return "searchsploit not installed — run: sudo apt install exploitdb"
    result = subprocess.run(
        f"searchsploit {keyword}",
        shell=True, capture_output=True, text=True)
    return result.stdout or "No results"

# ══════════════════════════════════════════════════════════════
# GITHUB SEARCH — Free API
# ══════════════════════════════════════════════════════════════

def search_github_pocs(cve_id: str) -> list:
    """Search GitHub for PoC exploits for a CVE."""
    try:
        r = requests.get(
            f"https://api.github.com/search/repositories"
            f"?q={cve_id}&sort=stars&order=desc",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10)
        return [{
            "name":  repo.get("full_name"),
            "url":   repo.get("html_url"),
            "stars": repo.get("stargazers_count"),
            "desc":  repo.get("description", "")[:100]
        } for repo in r.json().get("items", [])[:5]]
    except Exception as e:
        return [{"error": str(e)}]

# ══════════════════════════════════════════════════════════════
# SMART SEARCH — Auto-select best source + AI analysis
# ══════════════════════════════════════════════════════════════

def smart_search(query: str,
                 analyze: bool = True,
                 save_to_memory: bool = True) -> dict:
    """
    Smart search — auto-selects best sources.
    Uses AI to analyze and summarize results.
    Saves to memory for future context.
    """
    results      = {"query": query, "sources": {}}
    query_lower  = query.lower()

    # CVE/security search
    if any(k in query_lower for k in
           ["cve", "vulnerability", "exploit",
            "patch", "security advisory"]):
        results["sources"]["cves"]      = search_cves(query)
        results["sources"]["exploitdb"] = search_exploitdb(query)
        results["sources"]["github"]    = search_github_pocs(query)
        results["sources"]["web"]       = ddg_search(query)

    # Research/academic
    elif any(k in query_lower for k in
             ["research", "paper", "study",
              "arxiv", "academic"]):
        results["sources"]["arxiv"] = search_arxiv(query)
        results["sources"]["web"]   = ddg_search(query)

    # News
    elif any(k in query_lower for k in
             ["news", "latest", "recent",
              "today", "2026"]):
        results["sources"]["news"] = ddg_news(query)
        results["sources"]["web"]  = ddg_search(query)

    # General
    else:
        results["sources"]["web"]       = ddg_search(query)
        results["sources"]["wikipedia"] = search_wikipedia(query)

    # AI analysis
    if analyze and _modules_loaded:
        combined = json.dumps(
            results["sources"], indent=2,
            default=str)[:5000]
        analysis, model = call_ai(
            [{"role": "system", "content":
                "You are a research analyst. "
                "Analyze these search results and provide "
                "a clear, concise summary of key findings. "
                "Focus on the most relevant and reliable information."},
             {"role": "user", "content":
                f"Query: {query}\n\nResults:\n{combined}"}],
            ONLINE_POOL, label="search-analysis",
            max_tokens=1500
        )
        results["ai_analysis"] = analysis
        results["model_used"]  = model

    # Save to memory
    if save_to_memory and _modules_loaded:
        save_research(
            f"Search: {query}",
            results.get("ai_analysis",
                        str(results["sources"])[:1000]),
            tags=["search", query[:30]]
        )

    results["timestamp"] = datetime.now().isoformat()
    return results

def format_results(results: dict) -> str:
    """Format search results for display."""
    out   = f"## 🔍 Search: {results.get('query', '')}\n\n"
    sources = results.get("sources", {})

    if "web" in sources:
        out += "### Web Results\n"
        for r in sources["web"][:5]:
            if "error" not in r:
                out += (f"**{r.get('title')}**\n"
                        f"{r.get('url')}\n"
                        f"{r.get('snippet', '')[:200]}\n\n")

    if "cves" in sources:
        out += "### CVEs Found\n"
        for c in sources["cves"][:5]:
            if "error" not in c:
                out += (f"**{c.get('id')}** "
                        f"(CVSS: {c.get('score')})\n"
                        f"{c.get('desc', '')[:150]}\n\n")

    if "arxiv" in sources:
        out += "### Research Papers\n"
        for p in sources["arxiv"][:3]:
            if "error" not in p:
                out += (f"**{p.get('title')}**\n"
                        f"{p.get('summary', '')[:200]}\n\n")

    if "news" in sources:
        out += "### News\n"
        for n in sources["news"][:5]:
            if "error" not in n:
                out += (f"**{n.get('title')}** "
                        f"({n.get('date', '')})\n"
                        f"{n.get('snippet', '')[:200]}\n\n")

    if "ai_analysis" in results:
        out += f"### 🤖 AI Analysis\n{results['ai_analysis']}\n"

    return out

if __name__ == "__main__":
    query   = input("🔍 Search: ").strip()
    results = smart_search(query)
    print(format_results(results))
