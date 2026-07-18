# OCTA AI v1.0 — Advanced Usage Guide

A step-by-step guide to installing, configuring, and using every component
of this project. Written against the fixed/ready-to-run build.

> ⚠️ **Authorized use only.** The security/OSINT tooling in this project
> (Nmap, Nuclei, Nikto, sqlmap, subdomain enum, etc.) must only be pointed
> at systems you own or have explicit written authorization to test.
> Several menus in `security_agent.py` explicitly ask you to confirm
> authorization before running — that isn't decoration, it's the line
> between security research and a crime in most jurisdictions.

---

## 1. What's in this project

| File | Role |
|---|---|
| `agent.py` | Main CLI agent — 4-phase task loop (Discuss → Plan → Execute → Review), plus quick commands (search, image, vision, OSINT, CVE, TTS) |
| `bridge.py` | FastAPI server that exposes all providers as an OpenAI-compatible API — this is what Open WebUI talks to |
| `chainlit_app.py` | Web chat UI (Chainlit) — a Claude.ai-style interface in your browser |
| `security_agent.py` | Interactive menu for vuln scans, OWASP checks, CVE research, forensics, malware static analysis, bug-bounty recon |
| `osint_agent.py` | Domain/IP/username/GitHub OSINT recon, importable and standalone |
| `mcp_master.py` | MCP server exposing ~35 shell/recon/forensics tools to Claude Code or any MCP client |
| `websearch.py` | DuckDuckGo/Tavily search, CVE search, arXiv, Wikipedia |
| `specialized.py` | Image generation, vision analysis, TTS, CSV/log analysis, chart generation, sandboxed code execution |
| `memory.py` | ChromaDB-backed persistent memory (conversations, research, findings, tasks) |
| `outputs.py` | Report generation — Markdown, PDF, DOCX, HTML, JSON |
| `keys.py` | Shared API key pool + rotation logic used by everything above |
| `claude_code_setup.py` | Configures Claude Code to route through your OpenRouter key(s) |

All of these read/write relative paths (`memory/`, `outputs/`, `reports/`),
so **always run them from `~/agent/`** (the activation scripts handle this
for you — see Section 4).

---

## 2. Prerequisites

- Debian-based Linux: **Parrot OS or Kali Linux** (the installer uses `apt`
  and assumes their tool repos). Other Debian/Ubuntu systems will partially
  work but will miss some pentest tools.
- A regular user account with `sudo` access.
- Internet access for installation (Ollama models, pip/npm/go packages).
- At minimum 8 GB RAM if you want to run local Ollama models alongside
  everything else.

---

## 3. Install

```bash
unzip OCTA-AI-v1.0-READY.zip
cd octa-ai
chmod +x setup.sh
./setup.sh
```

`setup.sh` runs 9 steps and is safe to re-run if something fails partway
(it's idempotent — re-running won't duplicate config or crash):

1. **System update** — `apt update && apt upgrade`
2. **Core packages** — installs Nmap, Nikto, sqlmap, theHarvester, Gobuster,
   ffuf, Hydra, John, Hashcat, Wireshark, Binwalk, ClamAV, YARA, etc.
   Installed **one package at a time**, so if your distro's repos are
   missing one tool, everything else still installs (only that tool is
   skipped, with a warning telling you which one).
3. **Python packages** — installs from `requirements.txt`, also one at a
   time for the same reason. Only the packages the code actually imports
   are installed by default (litellm, fastapi, chainlit, chromadb, mcp,
   fpdf2, python-docx, ddgs, tavily-python, arxiv, wikipedia, pandas,
   matplotlib, pillow). Heavier, currently-unused extras (gradio,
   streamlit, langchain, openai, sentence-transformers, TTS/Coqui) are
   listed but **commented out** in `requirements.txt` — uncomment them
   yourself if you extend the code to use them.
4. **Ollama** — installs the local model runner and pulls two small
   free models (`phi3:mini`, `qwen2.5:3b`) so you have a working local
   fallback even with zero cloud API keys.
5. **Claude Code** — installs the `claude` CLI via npm.
6. **MCP servers** — filesystem + fetch MCP servers via npm.
7. **Go security tools** — Nuclei, a second Subfinder, waybackurls,
   Dalfox, subjs (fallback in case apt's versions in Step 2 were missing).
8. **Docker + Open WebUI** — starts Docker and launches the Open WebUI
   container on port 3000.
9. **Project setup** — creates `~/agent/` with subfolders
   (`outputs/`, `reports/`, `memory/`, `tools/`, `logs/`), copies every
   `.py`/`.sh`/config file there, writes `~/agent/activate.sh`, configures
   `~/.claude/settings.json`, and adds `source ~/agent/activate.sh` to
   your `.bashrc`.

At the end you'll see a summary telling you the setup finished and
reminding you that **no API keys ship with this repo** — you add your own
in the next step.

Sanity-check the install any time with:

```bash
bash ~/agent/test.sh
```

This checks that Python, Ollama, Claude Code, and every required Python
package are importable, and warns you if `keys.json` still has placeholder
values.

---

## 4. Configure your API keys

Open `~/agent/keys.json`. It looks like this out of the box:

```json
{
  "openrouter":  ["sk-or-v1-YOUR_NEW_KEY_1", "..."],
  "cerebras":    ["csk-YOUR_KEY_1", "..."],
  "grok":        ["xai-YOUR_KEY_1", "..."],
  "gemini":      ["YOUR_GEMINI_KEY_1", "..."],
  "requesty":    ["rqsty-sk-YOUR_KEY_1", "..."],
  "novita":      ["sk_YOUR_KEY_1", "..."],
  "huggingface": ["hf_YOUR_KEY"],
  "pollinations": ["sk_YOUR_KEY"],
  "cloudflare":  ["cfut_YOUR_KEY"]
}
```

**You only need ONE provider filled in to get started.** OpenRouter is the
easiest — it has a large free-model catalog on a single key
([openrouter.ai/keys](https://openrouter.ai/keys)). Delete the placeholder
strings you don't have a key for and leave that array empty (`[]`) — the
code treats a missing/empty provider as "skip and try the next one."

You can list **multiple keys per provider** (as arrays) — `keys.py`
round-robins through them automatically, which is how you get more free-tier
requests per day than a single key allows.

**Zero-key mode:** the code never crashes if every provider is left empty
— `call_ai()` just retries through empty/invalid keys, fails gracefully,
and returns an `"ERROR: All providers failed."` string instead of raising.
That said, only the agent's **Execute** phase is hard-wired to use local
Ollama (`EXECUTION_POOL`) regardless of cloud keys — Discuss/Plan/Review
and most standalone commands (`search`, `cve`, `osint`, chat UI, etc.) use
cloud-only pools and will return that error string until you add at least
one real key. In short: fill in one provider to get full functionality;
running with zero keys is only useful for testing the install itself.

Other places keys show up:

- `~/.claude/settings.json` — has a placeholder
  `"ANTHROPIC_API_KEY": "REPLACE_WITH_YOUR_OPENROUTER_KEY"`. Run
  `python3 ~/agent/claude_code_setup.py` after filling in `keys.json` and
  it will automatically rotate a real key into this file for you (see
  Section 9).

---

## 5. Start everything

```bash
source ~/.bashrc          # loads the activate.sh alias (only needed once per shell)
bash ~/agent/start_all.sh
```

This starts, in order:

1. **Ollama** (if not already running)
2. **MCP server** (`mcp_master.py`, backgrounded)
3. **Bridge API** (`bridge.py`, backgrounded, on port **8001**)
4. **Open WebUI** (Docker container, port **3000**, if not already running)

You'll see a confirmation summary with the URLs. To connect Open WebUI to
your local providers: open **http://localhost:3000** → Settings →
Connections → add `http://localhost:8001`.

Stop everything with:

```bash
bash ~/agent/stop_all.sh
```

(This kills `bridge.py`, `mcp_master.py`, `chainlit_app.py`, and `agent.py`
processes. Ollama and the Open WebUI Docker container keep running — stop
those separately with `pkill ollama` / `docker stop open-webui` if needed.)

---

## 6. Using the CLI agent (`agent.py`)

```bash
cd ~/agent && python3 agent.py
```

On launch it shows your free-tier capacity and a command list, then drops
you into a prompt:

```
💬 >
```

| Input | What it does |
|---|---|
| *(any plain text)* | Runs the full 4-phase agent loop: **Discuss → Plan → Execute → Review** on your task, using cloud models for reasoning and local Ollama for execution |
| `stream <task>` | Same as above but streams the response token-by-token |
| `search <query>` | Web search (DuckDuckGo, with Tavily as a fallback if you have that key) |
| `cve <service> [version]` | CVE lookup, e.g. `cve openssh 8.2` |
| `osint <domain>` | Runs domain recon + AI analysis of the results |
| `image <prompt>` | Generates an image via Pollinations.ai (free, no key needed) |
| `vision <path> [question]` | Analyzes a local image with Gemini vision, e.g. `vision ./screenshot.png what does this error mean?` |
| `tts <text>` | Text-to-speech (requires the optional `TTS` package — see Section 3, Step 3) |
| `capacity` | Reprints the free-tier capacity table |
| `setup-cc` | Runs Claude Code key setup inline |
| `quit` / `exit` / `q` | Exit |

**Example session:**

```
💬 > search latest CVEs in Apache Struts
💬 > cve struts 2.5
💬 > Write a Python script that parses an nmap XML report and lists open ports
```

Everything you do is saved to persistent memory (`~/agent/memory/`, backed
by ChromaDB) — conversations, research, and findings survive restarts.

---

## 7. Using the web chat UI (Chainlit)

```bash
cd ~/agent && chainlit run chainlit_app.py
```

Open **http://localhost:8000** in your browser. This gives you a
Claude.ai-style chat interface with:

- Model rotation across your configured providers (OpenRouter, Cerebras,
  Grok, Gemini)
- **File uploads**: drop in an image (jpg/png/gif/webp) for vision
  analysis, or a text file to have its contents included in your message
- Streaming responses

If you want it reachable on a different port or from other devices on your
network:

```bash
chainlit run chainlit_app.py --host 0.0.0.0 --port 8000
```

---

## 8. Security & OSINT tooling

### 8.1 Interactive menu

```bash
cd ~/agent && python3 security_agent.py
```

```
1. Vulnerability Scan (Nmap + Nuclei + Nikto + AI analysis)
2. OWASP Top 10 Complete Check
3. CVE Research + Intelligence
4. Digital Forensics (memory / file / network / disk artifact analysis)
5. Malware Static Analysis (run only inside an isolated VM!)
6. Bug Bounty Recon (extended)
7. OSINT (Domain / IP / Username / GitHub)
8. Show Past Findings (from memory)
9. Exit
```

Options **1, 2, and 6** will prompt you for an **authorization proof**
string before running anything against a target — have your engagement
letter/scope document reference ready to paste in. This is a manual
honor-system prompt, not a technical control, so the responsibility to
only test in-scope targets is still yours.

Every scan's findings are saved to memory (queryable via option 8) and can
be exported as a full report — see Section 10.

### 8.2 Standalone OSINT

```bash
cd ~/agent && python3 osint_agent.py
```

Prompts for a target and a type (`domain | ip | username | github | full`).
`full` runs domain recon + email harvesting + network recon in one pass and
prints a summary; the complete result is saved under `~/agent/reports/`.

You can also call these functions directly from your own scripts:

```python
from osint_agent import domain_recon, ip_recon, username_search, github_recon, full_osint

result = full_osint("example.com", "domain")
```

### 8.3 MCP tools (for Claude Code / any MCP client)

`mcp_master.py` exposes ~35 tools over MCP, grouped roughly as:

- **Shell**: `run`, `run_root`, `install`, `check`, `ensure`
- **Filesystem**: `read`, `write`, `append`, `ls`, `find`, `mkdir`, `hash_file`
- **Networking**: `net_info`, `public_ip`, `ping`, `nmap_scan`,
  `whois_lookup`, `dns_lookup`, `subdomain_enum`, `web_tech`, `dir_enum`,
  `nuclei_scan`, `ssl_scan`
- **Vuln research**: `searchsploit`, `get_cve`
- **Forensics**: `file_type`, `strings_extract`, `hex_dump`, `yara_scan`, `av_scan`
- **System**: `sys_info`, `processes`, `kill_process`, `apt_install`,
  `pip_install`, `go_install`
- **Misc**: `save_report`, `list_reports`, `download`, `extract`,
  `encode_base64`, `decode_base64`

This server is already registered in `~/.claude/settings.json` under
`mcpServers.parrot-master`, so once you run Claude Code (Section 9) it can
call these tools directly — e.g. asking it to *"nmap scan 10.0.0.5 and
summarize open ports"* will invoke `nmap_scan` through MCP automatically.

You can also point any other MCP-compatible client at it:

```bash
python3 ~/agent/mcp_master.py
```

---

## 9. Claude Code integration

```bash
python3 ~/agent/claude_code_setup.py
```

This reads a key from your `keys.json` OpenRouter list, rotates it into
`~/.claude/settings.json`, writes `~/agent/activate_cc.sh`, and prints the
config it applied. Then:

```bash
source ~/agent/activate_cc.sh
claude
```

Claude Code will now route through OpenRouter using one of your keys, with
the `parrot-master` MCP server (Section 8.3) already wired in. Re-run
`claude_code_setup.py` any time to rotate to a different key (useful if
one hits a rate limit).

---

## 10. Reports & output formats

`outputs.py` is used throughout the project to save results. It supports:

| Format | Function |
|---|---|
| Markdown | `save_markdown(content, filename)` |
| PDF | `save_pdf(content, filename)` |
| Word (.docx) | `save_docx(content, filename)` |
| HTML | `save_html(content, filename)` |
| JSON | `save_json(data, filename)` |
| All at once | `save_all_formats(content, filename)` |
| Full security report | `security_report(target, scan_type, findings, ...)` |

Everything lands under `~/agent/outputs/` or `~/agent/reports/` depending
on which module generated it. To generate a full multi-format security
report from your own script:

```python
from outputs import security_report
security_report("example.com", "vuln_scan", findings_list, [], "My Engagement")
```

---

## 11. Extra tools in `specialized.py`

```python
from specialized import (
    generate_image, analyze_image, extract_text_from_image,
    text_to_speech, analyze_csv, create_chart, analyze_log,
    run_python, run_bash
)
```

- `generate_image(prompt)` — free image generation via Pollinations.ai
- `analyze_image(path, question)` / `extract_text_from_image(path)` — OCR/vision via Gemini
- `text_to_speech(text)` — needs Coqui TTS installed (optional, heavy — see Section 3)
- `analyze_csv(path)` — AI-assisted CSV summarization (pandas)
- `create_chart(data)` — matplotlib chart generation
- `analyze_log(path)` — log file analysis
- `run_python(code)` / `run_bash(command)` — sandboxed-ish execution helpers
  used internally by the agent's "Execute" phase; **use with the same care
  as any code-execution tool** — don't feed it untrusted code.

---

## 12. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ModuleNotFoundError: No module named 'X'` | Re-run `pip3 install -r ~/agent/requirements.txt --break-system-packages`, or install that one package manually |
| Every cloud provider call returns `"ERROR: All providers failed."` | `keys.json` still has placeholder/empty values for every provider — check with `bash ~/agent/test.sh`. Only the agent's Execute phase automatically falls back to local Ollama; everything else needs at least one real cloud key |
| `mcp_master.py` fails to import | Confirm `pip3 show mcp` reports version ≥1.2.0 (older releases don't have `FastMCP`) |
| Output files scattered in your home directory instead of `~/agent/outputs`/`reports`/`memory` | You launched a script from somewhere other than `~/agent`. Always `cd ~/agent` first, or use `start_all.sh`/`activate.sh` which do this for you |
| Chainlit UI blank / won't load | Confirm you ran `chainlit run chainlit_app.py` **from inside `~/agent`**, not from your home directory |
| `duckduckgo` search returns nothing | The package was renamed to `ddgs` — `websearch.py` tries `ddgs` first automatically, but if neither is installed run `pip3 install ddgs --break-system-packages` |
| Docker/Open WebUI step fails | You may need to log out/in once after `usermod -aG docker` for group membership to take effect, or run with `sudo` |
| A specific apt package failed to install in Step 2 | Check the warning it printed — some tools (e.g. certain Go-based scanners) have a fallback install via `go install` in Step 7 |

---

## 13. Updating / re-running setup

`setup.sh` is safe to re-run any time — it won't duplicate your `.bashrc`
entry, and it will re-copy the latest `.py`/`.sh` files from wherever you
unzipped the project into `~/agent/`, overwriting the old copies there.
Your `~/agent/keys.json` **will also be overwritten** if you re-run it, so
back up your keys first if you've already filled them in:

```bash
cp ~/agent/keys.json ~/keys.json.backup
./setup.sh
cp ~/keys.json.backup ~/agent/keys.json
```
