"""
╔══════════════════════════════════════════════════════════════╗
║   Security Research Agent v1.0 — Fully Connected            ║
║   Imports: keys.py, memory.py, outputs.py,                  ║
║            websearch.py, osint_agent.py                    ║
║   Full key rotation | Auto-install | AI analysis            ║
║   Usage: python3 security_agent.py                          ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, json, subprocess, requests, shutil, hashlib, time
from datetime import datetime
from pathlib import Path

# ── Import ALL shared modules ─────────────────────────────────
from keys        import (call_ai, call_local, call_fast,
                         ONLINE_POOL, EXECUTION_POOL, rotate)
from memory      import (save_finding, save_research,
                         save_task, get_context, get_findings)
from outputs  import (save_all_formats, save_markdown,
                      save_pdf, security_report)
from websearch import search_cves, search_exploitdb, search_github_pocs
from osint_agent import (domain_recon, network_recon,
                          email_harvest, run, ensure)

# ══════════════════════════════════════════════════════════════
# SHARED HELPERS
# ══════════════════════════════════════════════════════════════

def ai_analyze(data: str, role: str, label: str = "") -> str:
    """Call online AI for security analysis."""
    result, model = call_ai(
        [{"role": "system", "content": role},
         {"role": "user",   "content": data}],
        ONLINE_POOL, label=label, max_tokens=4000
    )
    return result

def save_sec_report(target: str, report_type: str,
                    content: str, findings: list = [],
                    auth: str = "Authorized") -> str:
    """Save security report + to memory."""
    # Save to memory
    save_research(
        f"{report_type}: {target}",
        content[:500],
        tags=["security", report_type, target[:30]]
    )
    # Save report files
    return security_report(target, report_type,
                           findings, content, auth)

# ══════════════════════════════════════════════════════════════
# VULNERABILITY SCANNER
# ══════════════════════════════════════════════════════════════

def vuln_scan(target: str, auth: str) -> str:
    """
    AI-powered vulnerability scan.
    Uses all shared modules for analysis + reporting.
    """
    print(f"\n🔍 VULNERABILITY SCAN")
    print(f"   Target: {target}")
    print(f"   Auth:   {auth[:40]}...")
    print("   ⚠️  Authorized testing only!")
    print("="*55)

    # Get past intelligence from memory
    past = get_context(f"vulnerability {target}")
    results = {"target": target, "auth": auth}

    # Run scans
    steps = [
        ("nmap",    f"nmap -T4 -A -p- {target}",       300, "nmap"),
        ("nuclei",  f"nuclei -u {target} -severity critical,high,medium", 300, None),
        ("nikto",   f"nikto -h {target}",               300, "nikto"),
        ("whatweb", f"whatweb -a 3 {target}",            30,  "whatweb"),
        ("ssl",     f"sslscan {target}",                  60,  "sslscan"),
        ("headers", f"curl -sI http://{target}",          15,  None),
        ("dirs",    f"gobuster dir -u http://{target} "
                    f"-w /usr/share/wordlists/dirb/common.txt "
                    f"-q 2>/dev/null | head -30",         120, "gobuster"),
    ]

    for name, cmd, timeout, tool in steps:
        if tool:
            ensure(tool)
        print(f"   [{list(dict.fromkeys([s[0] for s in steps])).index(name)+1}/{len(steps)}] {name}...")
        results[name] = run(cmd, timeout)

    # CVE research for discovered services
    print("   → CVE research...")
    results["cves"] = search_cves(target, days_back=365)

    # ExploitDB search
    results["exploitdb"] = search_exploitdb(target)

    # AI Analysis using shared keys module
    system_prompt = (
        "Senior penetration tester with 15 years experience. "
        "Analyze these vulnerability scan results. Provide: "
        "1) Critical findings with CVSS scores "
        "2) Exploitation potential for each "
        "3) Attack chain possibilities "
        "4) Risk rating (Critical/High/Medium/Low) "
        "5) Prioritized remediation roadmap "
        "Human security team will review before any action."
    )
    if past:
        system_prompt += f"\n\nPrevious intelligence:\n{past}"

    combined = json.dumps(results, indent=2,
                          default=str)[:6000]
    analysis = ai_analyze(
        f"Target: {target}\nAuth: {auth}\n\n{combined}",
        system_prompt, "vuln-analysis"
    )

    # Save finding to memory
    save_finding(target, "vulnerability_scan",
                 analysis[:500], "high")

    # Generate report using outputs module
    report_path = save_sec_report(
        target, "vuln", analysis, [], auth)

    print(f"\n📋 KEY FINDINGS:\n{analysis[:500]}")
    return analysis

# ══════════════════════════════════════════════════════════════
# OWASP TOP 10 CHECKER
# ══════════════════════════════════════════════════════════════

def owasp_check(target: str, auth: str) -> str:
    """Complete OWASP Top 10 automated check."""
    print(f"\n🔐 OWASP TOP 10: {target}")
    checks = {}

    owasp_tests = [
        ("A01_Access_Control",
         f"gobuster dir -u http://{target} "
         f"-w /usr/share/wordlists/dirb/common.txt -q", 120, "gobuster"),

        ("A02_Crypto",
         f"sslscan {target}", 60, "sslscan"),

        ("A03_SQLi",
         f"sqlmap -u http://{target} --batch "
         f"--level=3 --risk=2 --dbs 2>/dev/null", 180, "sqlmap"),

        ("A03_XSS",
         f"dalfox url http://{target} --silence 2>/dev/null", 120, None),

        ("A05_Misconfig",
         f"nikto -h {target} -C all", 180, "nikto"),

        ("A05_Headers",
         f"curl -sI http://{target}", 15, None),

        ("A06_Components",
         f"whatweb -a 3 {target}", 30, "whatweb"),

        ("A07_Auth",
         f"curl -s http://{target}/admin "
         f"http://{target}/login "
         f"http://{target}/wp-admin 2>/dev/null | "
         f"grep -i 'login\\|admin\\|password' | head -5", 30, None),

        ("Nuclei_All",
         f"nuclei -u {target} -severity critical,high,medium", 300, None),

        ("A02_TLS",
         f"testssl.sh --quiet {target} 2>/dev/null | head -50", 120, None),
    ]

    for name, cmd, timeout, tool in owasp_tests:
        if tool:
            ensure(tool)
        print(f"   → {name}...")
        checks[name] = run(cmd, timeout)

    combined = json.dumps(checks, indent=2)[:7000]
    analysis = ai_analyze(
        f"Target: {target}\nAuth: {auth}\n\n{combined}",
        "OWASP Top 10 expert. For each OWASP category: "
        "✅ Pass / ❌ Fail / ⚠️ Partial. "
        "Include: CVSS score, evidence, remediation priority. "
        "Format as structured report.",
        "owasp"
    )

    # Save to memory and report
    save_finding(target, "owasp_check", analysis[:500])
    save_sec_report(target, "owasp", analysis, [], auth)
    print(f"\n📋 OWASP Summary:\n{analysis[:500]}")
    return analysis

# ══════════════════════════════════════════════════════════════
# CVE RESEARCH + INTELLIGENCE
# ══════════════════════════════════════════════════════════════

def cve_research(service: str, version: str = "") -> dict:
    """
    Deep CVE research using websearch module.
    Saves results to memory.
    """
    print(f"\n🔬 CVE Research: {service} {version}")

    # Get past research from memory
    past    = get_context(f"CVE {service} {version}")
    results = {
        "service":    service,
        "version":    version,
        "timestamp":  datetime.now().isoformat()
    }

    print("   → NVD API...")
    results["nvd"] = search_cves(f"{service} {version}")

    print("   → ExploitDB...")
    results["exploitdb"] = search_exploitdb(
        f"{service} {version}")

    print("   → GitHub PoCs...")
    if results["nvd"]:
        top_cve = results["nvd"][0].get("id", "")
        if top_cve:
            results["github_pocs"] = search_github_pocs(top_cve)

    # AI Analysis
    combined    = json.dumps(results, indent=2,
                             default=str)[:5000]
    system      = (
        "Vulnerability intelligence analyst. "
        "Analyze CVE data for authorized security research. "
        "Provide: critical CVEs ranked by severity, "
        "exploitation difficulty (1-10), "
        "patch/mitigation status, "
        "recommended defensive actions."
    )
    if past:
        system += f"\n\nPast research:\n{past}"

    analysis, model = call_ai(
        [{"role": "system", "content": system},
         {"role": "user",   "content": combined}],
        ONLINE_POOL, label="cve-research"
    )
    results["ai_analysis"] = analysis
    results["model_used"]  = model

    # Save to memory
    save_research(
        f"CVE: {service} {version}",
        analysis[:500],
        tags=["cve", service, version]
    )

    print(f"\n✅ CVE Analysis:\n{analysis[:500]}")
    return results

# ══════════════════════════════════════════════════════════════
# DIGITAL FORENSICS
# ══════════════════════════════════════════════════════════════

def forensics_analysis(evidence_path: str,
                        case_id: str,
                        analysis_type: str = "auto") -> str:
    """Digital forensics with full module integration."""
    print(f"\n🔬 FORENSICS: Case {case_id}")
    print(f"   Evidence: {evidence_path}")
    results = {}

    ext = Path(evidence_path).suffix.lower()

    # Memory analysis
    if analysis_type in ["memory", "auto"] and \
       ext in [".dmp", ".mem", ".raw", ".vmem"]:
        ensure("volatility3")
        for plugin in ["windows.pslist", "windows.netstat",
                       "windows.cmdline", "windows.malfind",
                       "windows.dlllist"]:
            print(f"   → {plugin}...")
            results[plugin] = run(
                f"volatility3 -f {evidence_path} {plugin}", 120)

    # File analysis
    if analysis_type in ["file", "auto"]:
        results["type"]    = run(f"file {evidence_path}")
        results["hash"]    = run(f"sha256sum {evidence_path}")
        results["strings"] = run(
            f"strings {evidence_path} | head -200")
        results["binwalk"] = run(f"binwalk {evidence_path}")

    # Network capture
    if analysis_type in ["network", "auto"] and ext == ".pcap":
        results["http"] = run(
            f"tcpdump -r {evidence_path} -A port 80 | head -50")
        results["dns"]  = run(
            f"tcpdump -r {evidence_path} port 53 | head -30")
        results["stats"] = run(
            f"tcpdump -r {evidence_path} -q | wc -l")

    # Disk image
    if analysis_type in ["disk", "auto"] and \
       ext in [".img", ".dd", ".iso"]:
        ensure("foremost")
        results["files"]   = run(f"fls -r {evidence_path} | head -50")
        results["recover"] = run(
            f"foremost -i {evidence_path} "
            f"-o ./recovered_{case_id}", 180)

    # AI Analysis using shared keys
    combined = json.dumps(results, indent=2,
                          default=str)[:5000]
    analysis = ai_analyze(
        f"Case: {case_id}\nEvidence: {evidence_path}\n\n{combined}",
        "Digital forensics expert. Analyze evidence. "
        "Provide: key findings, event timeline reconstruction, "
        "IOCs, anomalies, chain of custody notes, "
        "recommendations for investigation.",
        "forensics"
    )

    # Save to memory + report
    save_finding(
        case_id, "forensics",
        f"Evidence: {evidence_path}\n{analysis[:300]}"
    )
    save_sec_report(evidence_path, "forensics",
                    analysis, [], f"Case: {case_id}")

    print(f"\n✅ Forensics complete!")
    return analysis

# ══════════════════════════════════════════════════════════════
# MALWARE STATIC ANALYSIS
# ══════════════════════════════════════════════════════════════

def malware_analysis(filepath: str) -> str:
    """
    Static malware analysis — no code execution.
    Uses outputs module for professional reporting.
    """
    print(f"\n🦠 MALWARE STATIC ANALYSIS")
    print(f"   File: {filepath}")
    print("   ⚠️  Run in isolated VM for safety!")
    results = {}

    # File hashes
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        results["hashes"] = {
            "md5":    hashlib.md5(data).hexdigest(),
            "sha1":   hashlib.sha1(data).hexdigest(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "size":   f"{len(data):,} bytes"
        }
    except Exception as e:
        results["hashes"] = {"error": str(e)}

    # Static analysis tools
    tool_cmds = {
        "file_type": f"file {filepath}",
        "strings":   f"strings {filepath} | head -200",
        "imports":   f"objdump -p {filepath} 2>/dev/null || "
                     f"readelf -d {filepath} 2>/dev/null",
        "sections":  f"readelf -S {filepath} 2>/dev/null | head -30",
        "binwalk":   f"binwalk {filepath}",
        "entropy":   f"binwalk -E {filepath} 2>/dev/null | head -20",
        "yara":      f"yara /etc/yara/rules.yar {filepath} "
                     f"2>/dev/null || echo 'No YARA rules configured'",
        "av_scan":   f"clamscan {filepath}",
    }
    for name, cmd in tool_cmds.items():
        print(f"   → {name}...")
        results[name] = run(cmd)

    # VirusTotal lookup (if key available)
    vt_key = os.environ.get("VIRUSTOTAL_API_KEY", "")
    if vt_key and results.get("hashes", {}).get("sha256"):
        try:
            r = requests.get(
                f"https://www.virustotal.com/api/v3/files/"
                f"{results['hashes']['sha256']}",
                headers={"x-apikey": vt_key}, timeout=10)
            vt_data = r.json()
            stats   = (vt_data.get("data", {})
                      .get("attributes", {})
                      .get("last_analysis_stats", {}))
            results["virustotal"] = stats
        except Exception as e:
            results["virustotal"] = {"error": str(e)}

    # AI Analysis using shared keys (LOCAL for privacy)
    combined  = json.dumps(results, indent=2,
                           default=str)[:5000]
    system    = (
        "Malware reverse engineer. Analyze static analysis results. "
        "Provide: malware family classification, "
        "capabilities identified, "
        "IOCs (file hashes, strings, network indicators), "
        "MITRE ATT&CK techniques used, "
        "risk assessment, remediation recommendations."
    )
    # Use online AI for analysis (data is already hashes/strings)
    analysis = ai_analyze(combined, system, "malware")

    # Save to memory
    sha256 = results.get("hashes", {}).get("sha256", "unknown")
    save_finding(
        sha256, "malware_analysis",
        f"File: {filepath}\n{analysis[:300]}", "critical"
    )

    # Generate report
    findings = [{
        "type":     "Malware Sample",
        "severity": "Critical",
        "description": f"SHA256: {sha256}"
    }]
    save_sec_report(
        Path(filepath).name, "malware",
        analysis, findings, "Authorized Research"
    )

    print(f"\n✅ Malware analysis complete!")
    return analysis

# ══════════════════════════════════════════════════════════════
# BUG BOUNTY RECON
# ══════════════════════════════════════════════════════════════

def bugbounty_recon(target: str,
                    program: str,
                    scope: str) -> str:
    """
    Extended bug bounty reconnaissance.
    Uses osint_agent + websearch modules.
    """
    print(f"\n🎯 BUG BOUNTY: {program}")
    print(f"   Target: {target} | Scope: {scope}")
    results = {}

    # OSINT using shared osint module
    print("   → Domain intelligence...")
    results["domain"] = domain_recon(target)

    print("   → Email harvest...")
    results["emails"] = email_harvest(target)

    print("   → Network scan...")
    results["network"] = network_recon(target)

    # Web-specific recon
    print("   → Web application recon...")
    web_tools = [
        ("dirs",    f"gobuster dir -u http://{target} "
                    f"-w /usr/share/wordlists/dirb/big.txt -q", 180, "gobuster"),
        ("params",  f"arjun -u http://{target} --quiet 2>/dev/null", 60, None),
        ("xss",     f"dalfox url http://{target} --silence 2>/dev/null", 120, None),
        ("nuclei",  f"nuclei -u {target} -severity critical,high", 300, None),
        ("ssl",     f"sslscan {target}", 60, "sslscan"),
        ("wayback", f"waybackurls {target} 2>/dev/null | head -50", 60, None),
        ("js",      f"subjs -i <(echo http://{target}) 2>/dev/null | head -20", 60, None),
    ]
    for name, cmd, timeout, tool in web_tools:
        if tool:
            ensure(tool)
        print(f"   → {name}...")
        results[name] = run(cmd, timeout)

    # CVE research for program
    results["cves"] = search_cves(target, days_back=180)

    # AI Analysis focused on bounty
    combined = json.dumps(results, indent=2,
                          default=str)[:7000]
    analysis = ai_analyze(
        f"Program: {program}\n"
        f"Target: {target}\n"
        f"Scope: {scope}\n\n"
        f"Recon Data:\n{combined}",
        "Expert bug bounty hunter. Analyze recon data. "
        "Focus on: P1/P2 critical bugs, "
        "IDOR with sensitive data exposure, "
        "authentication bypass, RCE vectors, "
        "OAuth/SSO flaws, API security issues, "
        "business logic vulnerabilities. "
        "Only in-scope findings. "
        "For each: describe the bug, "
        "steps to reproduce, impact, CVSS score.",
        "bugbounty"
    )

    # Save to memory
    save_research(
        f"Bug Bounty: {program} — {target}",
        analysis[:500],
        tags=["bugbounty", program, target[:30]]
    )

    # Report
    save_sec_report(
        target, "bugbounty", analysis, [], program)

    print(f"\n📋 Key findings:\n{analysis[:600]}")
    return analysis

# ══════════════════════════════════════════════════════════════
# FULL OSINT (delegates to osint_agent)
# ══════════════════════════════════════════════════════════════

def quick_osint(target: str, target_type: str = "domain") -> str:
    """Quick OSINT using shared osint module."""
    from osint_agent import full_osint
    return full_osint(target, target_type)

# ══════════════════════════════════════════════════════════════
# SHOW PAST FINDINGS
# ══════════════════════════════════════════════════════════════

def show_findings(target: str = None) -> str:
    """Show past security findings from memory."""
    findings = get_findings(target)
    if not findings:
        return "No findings in memory yet."
    out = f"## Security Findings{f' for {target}' if target else ''}\n\n"
    for doc, meta in findings[:10]:
        out += (f"**Target:** {meta.get('target', 'N/A')} | "
                f"**Type:** {meta.get('type', 'N/A')} | "
                f"**Severity:** {meta.get('severity', 'N/A')}\n"
                f"{doc[:200]}\n\n")
    return out

# ══════════════════════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════════════════════

def show_menu():
    print("""
╔══════════════════════════════════════════════════════════════╗
║   Security Research Agent v1.0 — Fully Connected            ║
║   ⚠️  Authorized Testing Only — Always!                     ║
╠══════════════════════════════════════════════════════════════╣
║  1.  Vulnerability Scan (Nmap+Nuclei+Nikto+AI)              ║
║  2.  OWASP Top 10 Complete Check                            ║
║  3.  CVE Research + Intelligence                            ║
║  4.  Digital Forensics                                      ║
║  5.  Malware Static Analysis                                ║
║  6.  Bug Bounty Recon (Extended)                           ║
║  7.  OSINT (Domain/IP/Username)                            ║
║  8.  Show Past Findings (Memory)                           ║
║  9.  Exit                                                   ║
╚══════════════════════════════════════════════════════════════╝
""")

def main():
    show_menu()
    while True:
        choice = input("\nSelect (1-9): ").strip()

        if choice == "1":
            t = input("Target (authorized): ").strip()
            a = input("Authorization proof: ").strip()
            if t and a:
                vuln_scan(t, a)

        elif choice == "2":
            t = input("Target (authorized): ").strip()
            a = input("Authorization proof: ").strip()
            if t and a:
                owasp_check(t, a)

        elif choice == "3":
            s = input("Service name: ").strip()
            v = input("Version (optional): ").strip()
            cve_research(s, v)

        elif choice == "4":
            e = input("Evidence path: ").strip()
            c = input("Case ID: ").strip()
            t = input("Type (memory/file/network/disk/auto): ").strip() or "auto"
            if e and c:
                forensics_analysis(e, c, t)

        elif choice == "5":
            f = input("File path (in isolated VM): ").strip()
            if f:
                malware_analysis(f)

        elif choice == "6":
            t = input("Target (in-scope): ").strip()
            p = input("Program name: ").strip()
            s = input("Scope: ").strip()
            if t and p and s:
                bugbounty_recon(t, p, s)

        elif choice == "7":
            t  = input("Target: ").strip()
            tt = input("Type (domain/ip/username/github/full): ").strip() or "domain"
            if t:
                quick_osint(t, tt)

        elif choice == "8":
            t = input("Filter by target (blank for all): ").strip()
            print(show_findings(t or None))

        elif choice == "9":
            print("👋 Goodbye!")
            break

        else:
            print("Invalid choice. Enter 1-9.")

if __name__ == "__main__":
    main()
