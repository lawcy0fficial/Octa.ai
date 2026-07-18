"""
OSINT Agent v1.0 — Fully Connected
=====================================
Imports: keys.py, memory.py, outputs.py, websearch.py
Full key rotation | AI analysis | Auto-save reports
"""

import subprocess, json, requests, shutil
from datetime import datetime
from pathlib import Path

# ── Import shared modules ─────────────────────────────────────
from keys     import call_ai, call_fast, ONLINE_POOL, rotate
from memory   import save_osint, save_research, get_context
from outputs  import save_all_formats, save_markdown
from websearch import ddg_search, search_cves

# ══════════════════════════════════════════════════════════════
# TOOL HELPERS
# ══════════════════════════════════════════════════════════════

def run(cmd: str, timeout: int = 60) -> str:
    """Run system command."""
    try:
        r = subprocess.run(cmd, shell=True,
                          capture_output=True, text=True,
                          timeout=timeout)
        return r.stdout or r.stderr or "No output"
    except subprocess.TimeoutExpired:
        return f"Timeout after {timeout}s"
    except Exception as e:
        return f"Error: {e}"

def ensure(tool: str) -> bool:
    """Install tool if missing."""
    if shutil.which(tool):
        return True
    print(f"   📦 Installing {tool}...")
    r = subprocess.run(f"sudo apt install -y {tool}",
                      shell=True, capture_output=True)
    if r.returncode != 0:
        subprocess.run(
            f"pip3 install {tool} --break-system-packages",
            shell=True, capture_output=True)
    return shutil.which(tool) is not None

# ══════════════════════════════════════════════════════════════
# DOMAIN INTELLIGENCE
# ══════════════════════════════════════════════════════════════

def domain_recon(domain: str) -> dict:
    """Complete domain reconnaissance."""
    print(f"\n   🌐 Domain recon: {domain}")
    results = {}

    ensure("whois")
    results["whois"] = run(f"whois {domain}", 30)
    results["dns_a"]   = run(f"dig {domain} A +short")
    results["dns_mx"]  = run(f"dig {domain} MX +short")
    results["dns_ns"]  = run(f"dig {domain} NS +short")
    results["dns_txt"] = run(f"dig {domain} TXT +short")
    results["dns_all"] = run(f"dig {domain} ANY +noall +answer")

    ensure("subfinder")
    results["subdomains"] = run(
        f"subfinder -d {domain} -silent", 60)

    ensure("whatweb")
    results["tech"] = run(f"whatweb {domain}", 30)

    results["wayback"] = run(
        f"waybackurls {domain} 2>/dev/null | head -50", 30)

    # Certificate transparency
    try:
        r = requests.get(
            f"https://crt.sh/?q=%.{domain}&output=json",
            timeout=10)
        certs = r.json()[:10]
        results["certs"] = [
            c.get("name_value", "") for c in certs]
    except Exception:
        results["certs"] = []

    # Web search
    results["web_intel"] = ddg_search(
        f"{domain} security vulnerabilities", 3)

    return results

def email_harvest(domain: str) -> dict:
    """Email and username harvesting."""
    print(f"   📧 Harvesting: {domain}")
    results = {}
    ensure("theHarvester")
    results["harvester"] = run(
        f"theHarvester -d {domain} -b all -l 100", 120)
    return results

# ══════════════════════════════════════════════════════════════
# IP INTELLIGENCE
# ══════════════════════════════════════════════════════════════

def ip_recon(ip: str) -> dict:
    """IP address intelligence."""
    print(f"   🌐 IP recon: {ip}")
    results = {}

    results["rdns"] = run(f"dig -x {ip} +short")

    for api_url, key in [
        (f"https://ipinfo.io/{ip}/json", "ipinfo"),
        (f"https://ip-api.com/json/{ip}", "geo"),
    ]:
        try:
            r = requests.get(api_url, timeout=10)
            results[key] = r.json()
        except Exception:
            results[key] = {}

    # BGP/ASN info
    try:
        r = requests.get(
            f"https://api.bgpview.io/ip/{ip}", timeout=10)
        results["asn"] = r.json().get("data", {})
    except Exception:
        results["asn"] = {}

    results["nmap"] = run(f"nmap -T4 -A {ip}", 120)
    return results

# ══════════════════════════════════════════════════════════════
# USERNAME SEARCH
# ══════════════════════════════════════════════════════════════

def username_search(username: str) -> dict:
    """Search username across platforms."""
    print(f"   👤 Username search: {username}")
    platforms = {
        "GitHub":    f"https://github.com/{username}",
        "Twitter":   f"https://twitter.com/{username}",
        "LinkedIn":  f"https://linkedin.com/in/{username}",
        "Reddit":    f"https://reddit.com/u/{username}",
        "Instagram": f"https://instagram.com/{username}",
        "HackerOne": f"https://hackerone.com/{username}",
        "Bugcrowd":  f"https://bugcrowd.com/{username}",
        "GitLab":    f"https://gitlab.com/{username}",
    }

    found = []
    for platform, url in platforms.items():
        try:
            r = requests.get(
                url, timeout=5,
                headers={"User-Agent":
                    "Mozilla/5.0 (X11; Linux x86_64)"})
            if r.status_code == 200:
                found.append({"platform": platform, "url": url})
                print(f"   ✅ Found: {platform}")
        except Exception:
            pass

    return {
        "username": username,
        "found":    found,
        "total":    len(found)
    }

# ══════════════════════════════════════════════════════════════
# GITHUB INTELLIGENCE
# ══════════════════════════════════════════════════════════════

def github_recon(user_or_org: str) -> dict:
    """GitHub intelligence gathering."""
    print(f"   🐙 GitHub recon: {user_or_org}")
    base    = "https://api.github.com"
    headers = {"Accept": "application/vnd.github.v3+json"}
    results = {}

    try:
        r = requests.get(
            f"{base}/users/{user_or_org}",
            headers=headers, timeout=10)
        results["profile"] = r.json()

        r = requests.get(
            f"{base}/users/{user_or_org}/repos"
            "?sort=updated&per_page=10",
            headers=headers, timeout=10)
        results["repos"] = [{
            "name":     repo.get("name"),
            "desc":     repo.get("description"),
            "stars":    repo.get("stargazers_count"),
            "language": repo.get("language"),
            "url":      repo.get("html_url"),
            "updated":  repo.get("updated_at", "")[:10]
        } for repo in r.json()
          if isinstance(repo, dict)]

        # Search for sensitive files
        r = requests.get(
            f"{base}/search/code?q=user:{user_or_org}"
            "+filename:.env+OR+filename:config+OR+filename:secret",
            headers=headers, timeout=10)
        results["sensitive"] = r.json().get("items", [])[:5]

    except Exception as e:
        results["error"] = str(e)

    return results

# ══════════════════════════════════════════════════════════════
# NETWORK RECON (Authorized Only)
# ══════════════════════════════════════════════════════════════

def network_recon(target: str) -> dict:
    """Network-level recon — authorized targets only."""
    print(f"   🌐 Network recon: {target}")
    results = {}

    ensure("nmap")
    results["ports"]    = run(f"nmap -T4 -F --open {target}", 120)
    results["services"] = run(
        f"nmap -sV -T4 --top-ports 100 {target}", 120)
    ensure("wafw00f")
    results["waf"]      = run(f"wafw00f {target}", 30)

    # CVEs for discovered services
    results["cve_check"] = search_cves(target, days_back=365)
    return results

# ══════════════════════════════════════════════════════════════
# FULL OSINT — All in one
# ══════════════════════════════════════════════════════════════

def full_osint(target: str,
               target_type: str = "domain") -> str:
    """
    Complete OSINT investigation.
    Auto-saves to memory + generates report.
    """
    print(f"\n🔍 FULL OSINT: {target} ({target_type})")
    print("="*55)

    # Get memory context first
    context  = get_context(f"OSINT {target}")
    all_data = {
        "target":      target,
        "type":        target_type,
        "timestamp":   datetime.now().isoformat(),
        "past_intel":  context
    }

    if target_type == "domain":
        all_data["domain"]  = domain_recon(target)
        all_data["emails"]  = email_harvest(target)
        all_data["network"] = network_recon(target)

    elif target_type == "ip":
        all_data["ip"] = ip_recon(target)

    elif target_type == "username":
        all_data["username"] = username_search(target)
        all_data["github"]   = github_recon(target)

    elif target_type == "github":
        all_data["github"] = github_recon(target)

    elif target_type == "full":
        all_data["domain"]   = domain_recon(target)
        all_data["emails"]   = email_harvest(target)
        all_data["network"]  = network_recon(target)
        all_data["username"] = username_search(target)
        all_data["github"]   = github_recon(target)

    # AI Analysis using shared keys module
    print("\n   🤖 AI analyzing OSINT data...")
    combined = json.dumps(all_data, indent=2,
                          default=str)[:6000]

    # Add memory context to prompt
    system_prompt = (
        "You are an expert OSINT analyst. "
        "Analyze this intelligence data and provide: "
        "1) Key findings summary "
        "2) Interesting patterns or connections "
        "3) Security concerns identified "
        "4) Recommended follow-up research "
        "5) Risk assessment (High/Medium/Low)"
    )
    if context:
        system_prompt += (
            f"\n\nPrevious intelligence on this target:\n{context}")

    analysis, model = call_ai(
        [{"role": "system", "content": system_prompt},
         {"role": "user",   "content":
             f"Target: {target}\nType: {target_type}\n\n"
             f"Data:\n{combined}"}],
        ONLINE_POOL, label="osint-analysis"
    )

    # Save to memory using memory module
    save_osint(target, all_data)
    save_research(
        f"OSINT Analysis: {target}",
        analysis,
        tags=["osint", target_type, target[:30]]
    )

    # Generate report using outputs module
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = (
        f"# OSINT Report\n"
        f"**Target:** {target}\n"
        f"**Type:** {target_type}\n"
        f"**Date:** {datetime.now()}\n"
        f"**Model:** {model}\n\n"
        f"## AI Analysis\n{analysis}\n\n"
        f"## Raw Intelligence\n"
        f"```json\n{combined[:3000]}\n```"
    )

    # Save via outputs module
    Path("reports").mkdir(exist_ok=True)
    report_path = f"reports/osint_{target.replace('.','_')}_{ts}.md"
    save_markdown(report, f"OSINT: {target}", report_path)
    print(f"\n✅ Report: {report_path}")

    return analysis

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🔍 OSINT Agent v1.0")
    print("─"*40)
    print("Types: domain | ip | username | github | full")
    print()
    target = input("Target: ").strip()
    t_type = input("Type [domain]: ").strip() or "domain"
    result = full_osint(target, t_type)
    print(f"\n📋 Summary:\n{result[:800]}")
