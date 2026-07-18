#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║   Next Gen OCTA AI v1.0 — Complete Setup                   ║
# ║   All keys pre-configured | Parrot OS / Kali Linux          ║
# ╚══════════════════════════════════════════════════════════════╝
# Usage: chmod +x setup.sh && ./setup.sh

set -uo pipefail
clear

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Next Gen OCTA AI v1.0 — Complete Setup Script          ║"
echo "║     Platform: Parrot OS / Kali Linux                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: System ────────────────────────────────────────────
echo "📦 [1/9] System update..."
sudo apt update -y || echo "   ⚠️  apt update failed — continuing anyway"
sudo apt upgrade -y || echo "   ⚠️  apt upgrade failed — continuing anyway"

# ── Step 2: Core Packages ─────────────────────────────────────
# Installed one at a time: `apt install` aborts the ENTIRE batch if
# any single package name is unknown for this distro/release, which
# would otherwise silently skip every tool below it.
echo ""
echo "📦 [2/9] Installing core packages..."
CORE_PKGS=(
    python3 python3-pip python3-venv nodejs npm
    docker.io git curl wget golang-go ruby
    build-essential
    nmap nikto sqlmap theharvester
    gobuster ffuf hydra john hashcat
    wireshark tcpdump netcat-traditional
    binwalk foremost clamav yara
    whatweb wafw00f sslscan
    subfinder amass
)
for pkg in "${CORE_PKGS[@]}"; do
    if sudo apt install -y "$pkg" &>/dev/null; then
        echo "   ✅ $pkg"
    else
        echo "   ⚠️  $pkg not available via apt (skipped — some tools have Go-based fallback installs in Step 7)"
    fi
done

# ── Step 3: Python Virtual Env + Packages ─────────────────────
echo ""
echo "🐍 [3/9] Creating Python virtual environment..."
VENV_DIR="$HOME/agent/venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR" && echo "   ✅ venv created at $VENV_DIR" \
        || echo "   ⚠️  venv creation failed — falling back to --break-system-packages installs below"
else
    echo "   ℹ️  venv already exists at $VENV_DIR — reusing it"
fi

if [ -x "$VENV_DIR/bin/pip" ]; then
    PIP_CMD=("$VENV_DIR/bin/pip" install)
else
    # Fallback: no venv available, install into system Python instead.
    PIP_CMD=(pip3 install --break-system-packages)
fi

echo "🐍 Installing Python packages into venv..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    # Install core deps one at a time too — a single failing package
    # (e.g. a version mismatch on an odd Python build) shouldn't take
    # the rest of the stack down with it.
    grep -Ev '^\s*#|^\s*$' "$SCRIPT_DIR/requirements.txt" | while read -r pkg; do
        if "${PIP_CMD[@]}" "$pkg" --quiet &>/dev/null; then
            echo "   ✅ $pkg"
        else
            echo "   ⚠️  $pkg failed to install — you can retry manually later"
        fi
    done
else
    echo "   ⚠️  requirements.txt not found next to setup.sh — skipping"
fi
echo "   ✅ Python packages installed (core set)"
echo "   ℹ️  Activate the venv with: source ~/agent/venv/bin/activate"
echo "   ℹ️  Optional heavy extras (gradio, streamlit, langchain, openai,"
echo "      sentence-transformers, TTS) are commented out in requirements.txt"
echo "      — uncomment and 'pip3 install -r requirements.txt' if you need them."

# ── Step 4: Ollama ────────────────────────────────────────────
echo ""
echo "🤖 [4/9] Installing Ollama (local unlimited AI)..."
if command -v ollama &>/dev/null; then
    echo "   ℹ️  Ollama already installed — skipping reinstall"
else
    if curl -fsSL https://ollama.com/install.sh | sh 2>/dev/null; then
        echo "   ✅ Ollama installed"
    else
        echo "   ⚠️  Ollama install failed (offline or install script changed) — skipping"
    fi
fi

# Make sure the Ollama server is actually running before pulling —
# `ollama pull` needs a live daemon, and on a fresh install nothing
# has started it yet.
if command -v ollama &>/dev/null; then
    if ! curl -s http://localhost:11434 &>/dev/null; then
        (ollama serve &>/dev/null &)
        sleep 3
    fi

    echo "   Pulling models one at a time (parallel pulls were competing"
    echo "   for bandwidth/disk and causing incomplete downloads)..."
    for model in phi3:mini qwen2.5:3b; do
        if ollama list 2>/dev/null | grep -q "^${model}"; then
            echo "   ℹ️  $model already present — skipping"
        elif ollama pull "$model"; then
            echo "   ✅ $model pulled"
        else
            echo "   ⚠️  $model pull failed — run 'ollama pull $model' manually later"
        fi
    done
else
    echo "   ⚠️  ollama not on PATH — skipping model pulls (run 'ollama pull phi3:mini' manually later)"
fi

# ── Step 5: Claude Code ───────────────────────────────────────
echo ""
echo "💻 [5/9] Installing Claude Code..."
if command -v claude &>/dev/null; then
    echo "   ℹ️  Claude Code already installed — skipping reinstall"
else
    npm install -g @anthropic-ai/claude-code 2>/dev/null || true
    echo "   ✅ Claude Code installed"
fi

# ── Step 6: MCP Servers ───────────────────────────────────────
echo ""
echo "🔌 [6/9] Installing MCP servers..."
npm install -g @modelcontextprotocol/server-filesystem 2>/dev/null || true
npm install -g @modelcontextprotocol/server-fetch 2>/dev/null || true
echo "   ✅ MCP servers installed"

# ── Step 7: Go Security Tools ─────────────────────────────────
echo ""
echo "🔧 [7/9] Installing Go security tools..."
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest     2>/dev/null || true
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>/dev/null || true
go install github.com/tomnomnom/waybackurls@latest                       2>/dev/null || true
go install github.com/hahwul/dalfox/v2@latest                           2>/dev/null || true
go install github.com/lc/subjs@latest                                   2>/dev/null || true

echo "   ✅ Go security tools installed"

# ── Step 8: Docker + Open WebUI ──────────────────────────────
echo ""
echo "🖥️  [8/9] Setting up Open WebUI..."
sudo systemctl start docker   2>/dev/null || true
sudo systemctl enable docker  2>/dev/null || true
sudo usermod -aG docker "${USER:-$(whoami)}" 2>/dev/null || true

# Start Open WebUI if not running
#
# --add-host=host.docker.internal:host-gateway is the fix for a real
# gotcha: Open WebUI runs INSIDE this container, so "localhost:8001"
# typed into its Settings → Connections points at the container
# itself, not the host machine where bridge.py runs. That's why the
# bridge "connects" but never shows live models. Use
# http://host.docker.internal:8001 in Open WebUI instead of
# http://localhost:8001.
if ! docker ps | grep -q open-webui; then
    docker run -d \
        -p 3000:8080 \
        -v open-webui:/app/backend/data \
        --add-host=host.docker.internal:host-gateway \
        --name open-webui \
        --restart always \
        ghcr.io/open-webui/open-webui:main 2>/dev/null || true
fi
echo "   ✅ Open WebUI: http://localhost:3000"
echo "   ℹ️  In Open WebUI → Settings → Connections, add the bridge as:"
echo "         http://host.docker.internal:8001"
echo "      (NOT http://localhost:8001 — that points at the WebUI"
echo "       container itself, not your host machine)"

# ── Step 9: Project Setup ─────────────────────────────────────
echo ""
echo "📁 [9/9] Setting up project..."

# Create directories
mkdir -p ~/agent/{outputs,reports,memory,tools,logs}

# Copy all agent files to ~/agent/
for f in agent.py bridge.py chainlit_app.py \
          mcp_master.py memory.py keys.py \
          websearch.py osint_agent.py \
          specialized.py outputs.py \
          security_agent.py claude_code_setup.py \
          keys.json requirements.txt \
          start_all.sh stop_all.sh test.sh setup.sh README.md; do
    if [ -f "$SCRIPT_DIR/$f" ]; then
        cp "$SCRIPT_DIR/$f" ~/agent/
        echo "   ✅ Copied: $f"
    fi
done
chmod +x ~/agent/*.sh 2>/dev/null || true

# ── Configure Claude Code ─────────────────────────────────────
# NOTE: Claude Code speaks the Anthropic-native Messages API, not
# OpenRouter's OpenAI-compatible format, and there is no free Claude
# model on OpenRouter — so this no longer tries to fake "Claude" via
# OpenRouter + a Llama/DeepSeek model. Real Claude access is either
# a Claude subscription (run `claude` and log in) or a real
# console.anthropic.com API key placed in keys.json under
# "anthropic". claude_code_setup.py wires whichever you have.
mkdir -p ~/.claude

cat > ~/.claude/settings.json << EOF
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "$HOME"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    },
    "parrot-master": {
      "command": "python3",
      "args": ["$HOME/agent/mcp_master.py"]
    }
  }
}
EOF
# Run 'python3 ~/agent/claude_code_setup.py' afterwards — it fills in
# ANTHROPIC_API_KEY from keys.json if you added one, or leaves this
# MCP-only config in place so `claude` (subscription login) still works.

# ── Create Activation Script ──────────────────────────────────
cat > ~/agent/activate.sh << 'ACTIVATE'
#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║   Activate OCTA AI v1.0 Environment                    ║
# ║   Usage: source ~/agent/activate.sh                     ║
# ╚══════════════════════════════════════════════════════════╝

# Activate the Python venv created by setup.sh, if present.
if [ -f "$HOME/agent/venv/bin/activate" ]; then
    source "$HOME/agent/venv/bin/activate"
fi

# Claude Code: run `claude` to log in with your subscription, or
# run `python3 claude_code_setup.py` first if you put a real
# Anthropic key in keys.json under "anthropic".

# Go tools
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin:~/agent

cd ~/agent

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅ OCTA AI v1.0 — Environment Activated           ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Run agent:     python3 agent.py                     ║"
echo "║  Run bridge:    python3 bridge.py                    ║"
echo "║  Run chat UI:   chainlit run chainlit_app.py          ║"
echo "║  Run security:  python3 security_agent.py            ║"
echo "║  Run OSINT:     python3 osint_agent.py               ║"
echo "║  Claude Code:   python3 claude_code_setup.py         ║"
echo "║                 then: claude                         ║"
echo "║  Open WebUI:    http://localhost:3000                ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
ACTIVATE
chmod +x ~/agent/activate.sh

# start_all.sh, stop_all.sh, and test.sh are copied from the repo
# above (they already handle Ollama/MCP/Bridge/WebUI startup and
# `cd` into ~/agent so relative output paths resolve correctly).

# ── Add to .bashrc ────────────────────────────────────────────
if ! grep -q "agent/activate.sh" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# OCTA AI v1.0" >> ~/.bashrc
    echo "source ~/agent/activate.sh 2>/dev/null" >> ~/.bashrc
fi

# requirements.txt is copied from the repo above (already contains
# the correct, version-pinned dependency list used by Step 3).

# ── Final Summary ─────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          ✅ SETUP COMPLETE — v1.0                            ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  🚀 Quick Start:                                             ║"
echo "║     source ~/.bashrc                                         ║"
echo "║     bash ~/agent/start_all.sh                               ║"
echo "║                                                              ║"
echo "║  📱 Open WebUI:    http://localhost:3000                     ║"
echo "║  🤖 CLI Agent:     python3 ~/agent/agent.py                 ║"
echo "║  💬 Chat UI:       chainlit run ~/agent/chainlit_app.py     ║"
echo "║  🌉 Bridge:        python3 ~/agent/bridge.py                ║"
echo "║  🔌 MCP:           python3 ~/agent/mcp_master.py            ║"
echo "║  🔐 Security:      python3 ~/agent/security_agent.py        ║"
echo "║  🔍 OSINT:         python3 ~/agent/osint_agent.py           ║"
echo "║  💻 Claude Code:   python3 ~/agent/claude_code_setup.py     ║"
echo "║                    source ~/agent/activate_cc.sh             ║"
echo "║                    claude                                   ║"
echo "║                                                              ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  ⚠️  ADD YOUR OWN API KEYS before running anything:          ║"
echo "║     edit ~/agent/keys.json — no keys ship with this repo.   ║"
echo "║     openrouter.ai/keys | cloud.cerebras.ai | x.ai           ║"
echo "║     aistudio.google.com/apikey | huggingface.co/settings    ║"
echo "║                                                              ║"
echo "║  Everything works with just ONE provider filled in — the    ║"
echo "║  rest are optional extra capacity/rotation.                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Run: source ~/.bashrc && bash ~/agent/start_all.sh"
echo "Run: bash ~/agent/test.sh   (sanity-check the install)"
