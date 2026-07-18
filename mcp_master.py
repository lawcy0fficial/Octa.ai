"""
╔══════════════════════════════════════════════════════════════╗
║   MCP Master Server v1.0 — Enhanced Full Access             ║
║   Auto-install tools | Full Parrot OS | Security research   ║
║   Run: python3 mcp_master.py                                ║
╚══════════════════════════════════════════════════════════════╝
"""

from mcp.server.fastmcp import FastMCP
import subprocess, os, json, shutil, hashlib, requests
from pathlib import Path
from datetime import datetime

server = FastMCP("parrot-master")

# ── Core Shell ────────────────────────────────────────────────

@server.tool()
def run(command: str, timeout: int = 120) -> str:
    """Run any system command on Parrot OS."""
    try:
        r = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=timeout,
            cwd=os.path.expanduser("~"))
        return r.stdout or r.stderr or "Done (no output)"
    except subprocess.TimeoutExpired:
        return f"Timeout after {timeout}s"
    except Exception as e:
        return f"Error: {e}"

@server.tool()
def run_root(command: str, timeout: int = 120) -> str:
    """Run command with sudo."""
    return run(f"sudo {command}", timeout)

@server.tool()
def install(tool: str) -> str:
    """Auto-install tool via apt/pip/gem/go/snap."""
    if shutil.which(tool):
        return f"✅ {tool} already installed"
    for method, cmd in [
        ("apt",  f"sudo apt install -y {tool}"),
        ("pip",  f"pip3 install {tool} --break-system-packages"),
        ("gem",  f"gem install {tool}"),
        ("go",   f"go install {tool}@latest"),
        ("snap", f"sudo snap install {tool}"),
    ]:
        r = subprocess.run(cmd, shell=True,
                          capture_output=True, timeout=120)
        if r.returncode == 0:
            return f"✅ {tool} installed via {method}"
    return f"❌ Could not install {tool}"

@server.tool()
def check(tool: str) -> str:
    """Check if tool is installed."""
    path = shutil.which(tool)
    return f"✅ {tool} → {path}" if path else f"❌ {tool} not found"

@server.tool()
def ensure(tool: str) -> str:
    """Install tool if missing, return status."""
    if shutil.which(tool):
        return f"✅ {tool} ready"
    return install(tool)

# ── File Operations ───────────────────────────────────────────

@server.tool()
def read(path: str) -> str:
    """Read file contents."""
    try:
        return Path(os.path.expanduser(path)).read_text(
            encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error: {e}"

@server.tool()
def write(path: str, content: str) -> str:
    """Write content to file."""
    try:
        p = Path(os.path.expanduser(path))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"✅ Written: {p} ({len(content)} chars)"
    except Exception as e:
        return f"Error: {e}"

@server.tool()
def append(path: str, content: str) -> str:
    """Append content to file."""
    try:
        with open(os.path.expanduser(path), "a") as f:
            f.write(content)
        return f"✅ Appended to {path}"
    except Exception as e:
        return f"Error: {e}"

@server.tool()
def ls(path: str = "~") -> str:
    """List directory."""
    return run(f"ls -la {os.path.expanduser(path)}")

@server.tool()
def find(path: str, pattern: str = "*") -> str:
    """Find files matching pattern."""
    return run(f"find {os.path.expanduser(path)} -name '{pattern}' 2>/dev/null")

@server.tool()
def mkdir(path: str) -> str:
    """Create directory."""
    try:
        Path(os.path.expanduser(path)).mkdir(parents=True, exist_ok=True)
        return f"✅ Created: {path}"
    except Exception as e:
        return f"Error: {e}"

@server.tool()
def hash_file(path: str) -> str:
    """Get file hashes."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        return json.dumps({
            "md5":    hashlib.md5(data).hexdigest(),
            "sha1":   hashlib.sha1(data).hexdigest(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "size":   len(data)
        }, indent=2)
    except Exception as e:
        return f"Error: {e}"

# ── Network ───────────────────────────────────────────────────

@server.tool()
def net_info() -> str:
    """Get network information."""
    return json.dumps({
        "interfaces": run("ip addr show"),
        "routes":     run("ip route"),
        "connections": run("ss -tulpn"),
        "arp":        run("arp -a"),
        "dns":        run("cat /etc/resolv.conf"),
    }, indent=2)

@server.tool()
def public_ip() -> str:
    """Get public IP."""
    return run("curl -s ifconfig.me", 10)

@server.tool()
def ping(host: str, count: int = 4) -> str:
    """Ping a host."""
    return run(f"ping -c {count} {host}", 30)

# ── System ────────────────────────────────────────────────────

@server.tool()
def sys_info() -> str:
    """Get system information."""
    return json.dumps({
        "os":     run("uname -a"),
        "distro": run("cat /etc/os-release"),
        "cpu":    run("lscpu | head -15"),
        "memory": run("free -h"),
        "disk":   run("df -h"),
        "uptime": run("uptime"),
    }, indent=2)

@server.tool()
def processes() -> str:
    """Get running processes."""
    return run("ps aux --sort=-%mem | head -25")

@server.tool()
def kill_process(pid: int) -> str:
    """Kill a process by PID."""
    return run(f"kill {pid}")

# ── Package Management ────────────────────────────────────────

@server.tool()
def apt_install(package: str) -> str:
    """Install via apt."""
    return run(f"sudo apt install -y {package}", 180)

@server.tool()
def pip_install(package: str) -> str:
    """Install via pip."""
    return run(
        f"pip3 install {package} --break-system-packages", 120)

@server.tool()
def go_install(package: str) -> str:
    """Install via go."""
    return run(f"go install {package}@latest", 120)

# ── Security Research Tools ───────────────────────────────────

@server.tool()
def nmap_scan(target: str, options: str = "-T4 -F") -> str:
    """Run nmap scan on authorized target."""
    ensure("nmap")
    return run(f"nmap {options} {target}", 300)

@server.tool()
def whois_lookup(domain: str) -> str:
    """WHOIS lookup."""
    ensure("whois")
    return run(f"whois {domain}", 30)

@server.tool()
def dns_lookup(domain: str, record: str = "ANY") -> str:
    """DNS lookup."""
    return run(f"dig {domain} {record} +noall +answer")

@server.tool()
def subdomain_enum(domain: str) -> str:
    """Enumerate subdomains."""
    ensure("subfinder")
    return run(f"subfinder -d {domain} -silent", 60)

@server.tool()
def web_tech(url: str) -> str:
    """Identify web technologies."""
    ensure("whatweb")
    return run(f"whatweb -a 3 {url}", 30)

@server.tool()
def dir_enum(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt") -> str:
    """Directory enumeration."""
    ensure("gobuster")
    return run(
        f"gobuster dir -u {url} -w {wordlist} -q", 180)

@server.tool()
def nuclei_scan(target: str, severity: str = "critical,high") -> str:
    """Run Nuclei vulnerability scanner."""
    return run(
        f"nuclei -u {target} -severity {severity}", 300)

@server.tool()
def ssl_scan(target: str) -> str:
    """Analyze SSL/TLS."""
    ensure("sslscan")
    return run(f"sslscan {target}", 60)

@server.tool()
def searchsploit(keyword: str) -> str:
    """Search ExploitDB."""
    ensure("searchsploit")
    return run(f"searchsploit {keyword}", 30)

@server.tool()
def get_cve(cve_id: str) -> str:
    """Get CVE details from NVD."""
    try:
        r = requests.get(
            f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}",
            timeout=10)
        return json.dumps(r.json(), indent=2)[:2000]
    except Exception as e:
        return f"Error: {e}"

# ── File Analysis ─────────────────────────────────────────────

@server.tool()
def file_type(path: str) -> str:
    """Check file type."""
    return run(f"file {path}")

@server.tool()
def strings_extract(path: str, min_len: int = 4) -> str:
    """Extract strings from binary."""
    return run(f"strings -n {min_len} {path} | head -200")

@server.tool()
def hex_dump(path: str, lines: int = 50) -> str:
    """Get hex dump."""
    return run(f"hexdump -C {path} | head -{lines}")

@server.tool()
def yara_scan(filepath: str, rules: str = "/etc/yara/rules.yar") -> str:
    """YARA scan."""
    return run(f"yara {rules} {filepath} 2>/dev/null || echo 'No rules'")

@server.tool()
def av_scan(filepath: str) -> str:
    """ClamAV scan."""
    ensure("clamav")
    return run(f"clamscan {filepath}")

# ── Reports ───────────────────────────────────────────────────

@server.tool()
def save_report(content: str, name: str) -> str:
    """Save report to reports directory."""
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(f"reports/{name}_{ts}.md")
    path.parent.mkdir(exist_ok=True)
    path.write_text(content)
    return f"✅ Report: {path}"

@server.tool()
def list_reports() -> str:
    """List saved reports."""
    p = Path("reports")
    if not p.exists():
        return "No reports directory"
    files = sorted(p.glob("*"))
    return "\n".join(str(f) for f in files) or "No reports"

# ── Utilities ─────────────────────────────────────────────────

@server.tool()
def download(url: str, output: str = "/tmp/download") -> str:
    """Download file."""
    return run(f"wget -q '{url}' -O '{output}'", 60)

@server.tool()
def extract(archive: str, dest: str = "/tmp/extracted") -> str:
    """Extract archive."""
    return run(
        f"mkdir -p {dest} && "
        f"tar -xf {archive} -C {dest} 2>/dev/null || "
        f"unzip {archive} -d {dest} 2>/dev/null", 60)

@server.tool()
def encode_base64(text: str) -> str:
    """Base64 encode text."""
    import base64
    return base64.b64encode(text.encode()).decode()

@server.tool()
def decode_base64(text: str) -> str:
    """Base64 decode text."""
    import base64
    try:
        return base64.b64decode(text).decode()
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║   MCP Master Server v1.0 — Starting                         ║
║   Full Parrot OS Access | Auto-install | Security Tools     ║
╚══════════════════════════════════════════════════════════════╝
""")
    server.run()
