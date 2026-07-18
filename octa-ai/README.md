<div align="center">

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    ██████╗  ██████╗████████╗ █████╗      █████╗ ██╗        ║
║   ██╔═══██╗██╔════╝╚══██╔══╝██╔══██╗    ██╔══██╗██║        ║
║   ██║   ██║██║        ██║   ███████║    ███████║██║        ║
║   ██║   ██║██║        ██║   ██╔══██║    ██╔══██║██║        ║
║   ╚██████╔╝╚██████╗   ██║   ██║  ██║    ██║  ██║██║        ║
║    ╚═════╝  ╚═════╝   ╚═╝   ╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝        ║
║                                                              ║
║         Omnipotent Cyber Threat Analysis AI                 ║
║                    Version 1.0                              ║
╚══════════════════════════════════════════════════════════════╝
```

# OCTA AI v1.0

**Omnipotent Cyber Threat Analysis AI**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Parrot%20OS%20%7C%20Kali-red.svg)]()
[![Cost](https://img.shields.io/badge/Cost-%240%2Fmonth-green.svg)]()
[![APIs](https://img.shields.io/badge/Free%20APIs-82%2C500%2B%20req%2Fday-orange.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()

> *Inspired by Claude.ai — Built for Security Researchers*
> *8 Powers. 1 Agent. $0/month forever.*

</div>

---

## 🐙 What is OCTA AI?

OCTA AI is a **Next Generation Personal AI Agent** built for professional
security researchers. Like an octopus with 8 arms, OCTA AI operates
across 8 powerful domains simultaneously — all powered by **82,500+
free API requests per day** with **zero monthly cost**.

### The 8 Powers of OCTA AI

```
Arm 1: 🧠 Discussion & Deep Analysis
Arm 2: 📋 Strategic Planning
Arm 3: ⚙️  Agentic Code Execution (Never Stops)
Arm 4: ✅ Quality Review & Polish
Arm 5: 🔐 Security Research & Penetration Testing
Arm 6: 🔍 OSINT & Intelligence Gathering
Arm 7: 🎨 Image Generation & Voice Synthesis
Arm 8: 📄 Professional Report Generation
```

---

## ✨ Key Features

### 🤖 AI Capabilities
- **Multi-provider rotation** — 82,500+ free requests/day
- **Agentic coding loop** — never stops until task complete
- **Auto-fixes syntax errors** — self-correcting code generation
- **Persistent memory** — remembers across sessions (ChromaDB)
- **Streaming responses** — word-by-word like Claude.ai
- **Vision** — analyze images, screenshots, evidence
- **Web search** — real-time CVE + web intelligence

### 🔐 Security Research
- **Vulnerability scanning** — Nmap + Nuclei + Nikto + AI analysis
- **OWASP Top 10** — complete automated A01-A10 checks
- **CVE research** — NVD + ExploitDB + GitHub PoCs
- **Digital forensics** — memory, disk, network analysis
- **Malware analysis** — static analysis + AI classification
- **Bug bounty recon** — extended recon + P1/P2 focus
- **OSINT automation** — domain, IP, username, GitHub intel

### 🎨 Creative & Productivity
- **Image generation** — Pollinations.ai (100% free, no key)
- **Voice synthesis** — Coqui TTS (local, unlimited)
- **Data analysis** — CSV/log analysis with AI insights
- **Multi-format output** — PDF, MD, DOCX, HTML auto-saved

### 🖥️ Interface Options
- **Open WebUI** — Claude.ai-like GUI at localhost:3000
- **Chainlit** — Lightweight chat UI at localhost:8000
- **CLI** — Direct terminal interface
- **API Bridge** — OpenAI-compatible at localhost:8001

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT                                │
│         Open WebUI / Chainlit / CLI                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │     🧠 DISCUSSION          │ ← OpenRouter×10
         │     Deep Analysis          │   Cerebras×9
         └─────────────┬─────────────┘   Grok×9 + Gemini×7
                       │
         ┌─────────────▼─────────────┐
         │     📋 PLANNING            │ ← Fastest providers
         │     Strategy & Blueprint   │   Cerebras + Gemini
         └─────────────┬─────────────┘
                       │
         ┌─────────────▼─────────────┐
         │     ⚙️  EXECUTION          │ ← LOCAL OLLAMA ONLY
         │     Agentic Never-Stop Loop│   Unlimited + Private
         │     Auto-fix Errors        │   No Content Filters
         └─────────────┬─────────────┘
                       │
         ┌─────────────▼─────────────┐
         │     ✅ REVIEW              │ ← All providers
         │     Quality Polish         │   rotating
         └─────────────┬─────────────┘
                       │
         ┌─────────────▼─────────────┐
         │     🔗 MCP LAYER           │
         │     Full Parrot OS Access  │
         │     Auto-install tools     │
         └─────────────┬─────────────┘
                       │
         ┌─────────────▼─────────────┐
         │     📄 OUTPUT              │
         │  .py .md .pdf .docx .html  │
         └─────────────────────────────┘
```

---

## 📦 Module Map

```
keys.py ──────────────── 🔑 Base: All keys + call_ai()
memory.py ────────────── 🧠 Base: ChromaDB persistence
outputs.py ───────────── 📄 Base: PDF/MD/DOCX/HTML
websearch.py ◄─ keys + memory ── 🔍 Search + CVE
osint_agent.py ◄─ all above ──── 🕵️  OSINT automation
specialized.py ◄─ all above ──── 🎨 Image+Voice+Data
security_agent.py ◄─ ALL ──────── 🔐 Security research
agent.py ◄────────── keys ──────── 🤖 Main controller
bridge.py ◄────────── keys ──────── 🌉 Open WebUI bridge
chainlit_app.py ◄── keys+memory ── 💬 Chat interface
mcp_master.py ────────────────────── 🔌 Parrot OS tools
```

---

## 🚀 Quick Start

### Prerequisites
- Parrot OS or Kali Linux
- 8GB RAM minimum
- Internet connection
- Fresh API keys (see below)

### Installation

```bash
# 1. Clone or extract
git clone https://github.com/YOUR_USERNAME/octa-ai
cd octa-ai

# 2. Add your API keys to keys.json

# 3. One-click setup
chmod +x setup.sh && ./setup.sh

# 4. Test everything
bash test.sh

# 5. Start OCTA AI
bash start_all.sh
```

### Access
```
Open WebUI:  http://localhost:3000
Chainlit:    chainlit run chainlit_app.py
CLI Agent:   python3 agent.py
Security:    python3 security_agent.py
OSINT:       python3 osint_agent.py
```

---

## 💬 Agent Commands

| Command | Description |
|---------|-------------|
| `[any text]` | Run 4-phase OCTA AI agent |
| `stream [text]` | Word-by-word streaming |
| `image [prompt]` | Generate image (Pollinations.ai) |
| `vision [path] [q]` | Analyze image with AI |
| `search [query]` | Web search + AI analysis |
| `cve [service] [ver]` | CVE research (NVD+ExploitDB) |
| `osint [domain]` | Full OSINT automation |
| `tts [text]` | Text to speech (local) |
| `setup-cc` | Configure Claude Code |
| `capacity` | Show API capacity |

---

## 📊 Free API Capacity

| Provider | Keys | Daily Limit | Speed |
|----------|------|-------------|-------|
| OpenRouter | ×10 | 56,000 req/day | Varies |
| Cerebras | ×9 | ~9M tokens/day | ⚡ 2,000 tok/s |
| Grok/xAI | ×9 | Large capacity | Fast |
| Gemini | ×7 | 10,500 req/day | Fast (1M ctx) |
| Requesty | ×10 | 16,000 req/day | Fast |
| Novita | ×8 | Free tier | Fast |
| HuggingFace | ×1 | 2,000 req/day | Moderate |
| **Ollama** | **♾️** | **UNLIMITED** | **Local** |

**Total: ~82,500+ requests/day FREE**

---

## 🔑 API Keys Setup

Get your free API keys:

| Platform | URL | Keys Needed |
|----------|-----|-------------|
| OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) | 10 |
| Cerebras | [cloud.cerebras.ai](https://cloud.cerebras.ai) | 9 |
| Grok/xAI | [x.ai/api](https://x.ai/api) | 9 |
| Gemini | [aistudio.google.com](https://aistudio.google.com/apikey) | 7 |
| Requesty | [requesty.ai](https://requesty.ai) | 10 |
| Novita | [novita.ai](https://novita.ai) | 8 |
| HuggingFace | [huggingface.co](https://huggingface.co/settings/tokens) | 1 |

Update `keys.json` with your keys.

---

## 🔐 Security Research Modules

> ⚠️ **All security tools require explicit written authorization.**
> Never test systems without permission. Authorized research only.

| Module | Capabilities |
|--------|-------------|
| Vulnerability Scanner | Nmap + Nuclei + Nikto + AI CVSS scoring |
| OWASP Top 10 | Complete A01-A10 automated checks |
| CVE Research | NVD + ExploitDB + GitHub PoC lookup |
| Digital Forensics | Memory/Disk/Network/File analysis |
| Malware Analysis | Static analysis + AI classification |
| Bug Bounty Recon | Extended recon + P1/P2 bug focus |
| OSINT Engine | Domain/IP/Username/GitHub intelligence |

---

## 🤖 Ollama Local Models

```bash
# Install (runs locally = unlimited + private)
curl -fsSL https://ollama.com/install.sh | sh

# Pull models for 8GB RAM
ollama pull phi3:mini     # 2GB — fast
ollama pull qwen2.5:3b    # 2GB — better quality
```

---

## 📁 Project Structure

```
octa-ai/
├── 🔑 keys.py              # Shared keys + AI calls (BASE)
├── 🧠 memory.py            # ChromaDB persistence (BASE)
├── 📄 outputs.py           # Report generation (BASE)
├── 🤖 agent.py             # Main OCTA AI agent
├── 🌉 bridge.py            # Open WebUI bridge
├── 💬 chainlit_app.py      # Chat interface
├── 🔌 mcp_master.py        # Parrot OS MCP (30+ tools)
├── 🔍 websearch.py         # Web search + CVE
├── 🕵️  osint_agent.py      # OSINT automation
├── 🎨 specialized.py       # Image + Voice + Data
├── 🔐 security_agent.py    # Security research
├── 💻 claude_code_setup.py # Claude Code config
├── ⚙️  setup.sh             # One-click setup
├── 🚀 start_all.sh         # Start everything
├── ⏹️  stop_all.sh          # Stop everything
├── 🧪 test.sh              # Verify installation
├── 🔑 keys.json            # API keys (update this!)
├── 📦 requirements.txt     # Dependencies
└── 📖 README.md            # This file
```

---

## 🛠️ Tech Stack

```
AI Framework:   LiteLLM (100+ providers unified)
Memory:         ChromaDB (vector database)
GUI:            Open WebUI + Chainlit
API Bridge:     FastAPI + Uvicorn
Local AI:       Ollama (phi3:mini, qwen2.5:3b)
MCP:            Model Context Protocol
Reports:        fpdf2 + python-docx
Search:         DuckDuckGo + NVD API
Image Gen:      Pollinations.ai (free)
Voice:          Coqui TTS (local)
Platform:       Parrot OS / Kali Linux
```

---

## ⚖️ Legal Disclaimer

OCTA AI is designed for **authorized security research only**.

- All penetration testing requires written authorization
- Bug bounty hunting must be within program scope
- Digital forensics requires legal authorization
- Malware analysis in isolated environments only
- Never test systems without explicit permission

---

## 👨‍💻 Author

**Security Researcher**
- GitHub: [github.com/lawcy0fficial](https://github.com/lawcy0fficial)
- Portfolio: [shibinoffi.github.io](https://shibinoffi.github.io)

---

## 📄 License

MIT License — Free for authorized security research and personal use.

---

<div align="center">

**⚡ OCTA AI — 8 Powers. 1 Agent. $0/month. ⚡**

*Built with ❤️ for the security research community*

</div>
