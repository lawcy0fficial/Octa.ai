#!/bin/bash
echo "🧪 Testing OCTA AI v1.0..."

# Packages were installed into ~/agent/venv by setup.sh — activate it
# so these checks use the right python3/pip, not the system ones.
if [ -f "$HOME/agent/venv/bin/activate" ]; then
    source "$HOME/agent/venv/bin/activate"
    echo "   ℹ️  Using venv: $HOME/agent/venv"
else
    echo "   ⚠️  No venv found at ~/agent/venv — testing system python3 instead"
fi

PASS=0; FAIL=0

check() {
  if eval "$2" &>/dev/null; then echo "   ✅ $1"; ((PASS++))
  else echo "   ❌ $1"; ((FAIL++)); fi
}

check "Python 3"       "python3 --version"
check "Ollama"         "ollama --version"
check "Claude Code"    "claude --version"
check "litellm"        "python3 -c 'import litellm'"
check "fastapi"        "python3 -c 'import fastapi'"
check "chainlit"       "python3 -c 'import chainlit'"
check "chromadb"       "python3 -c 'import chromadb'"
check "fpdf2"          "python3 -c 'import fpdf'"
check "python-docx"    "python3 -c 'import docx'"
check "duckduckgo search"  "python3 -c 'import ddgs' 2>/dev/null || python3 -c 'import duckduckgo_search'"
check "keys.json"      "test -f keys.json"
check "keys.py"        "test -f keys.py"
check "agent.py"       "test -f agent.py"
check "memory.py"      "test -f memory.py"
check "nmap"           "nmap --version"
check "Ollama phi3"    "ollama list | grep phi3"
check "Module imports" "python3 -c 'from keys import call_ai; print(\"OK\")'"
check "Bridge reachable (host)" "curl -sf http://localhost:8001/health"
if command -v docker &>/dev/null && docker ps 2>/dev/null | grep -q open-webui; then
    check "Bridge reachable FROM Open WebUI container" \
        "docker exec open-webui curl -sf http://host.docker.internal:8001/health"
fi

if grep -q "YOUR_KEY\|REPLACE_WITH" keys.json 2>/dev/null; then
  echo "   ⚠️  keys.json still has placeholder values — edit it and add"
  echo "      at least one real API key (or rely on local Ollama only)."
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "✅ Ready! Run: bash start_all.sh" \
                || echo "⚠️  Run: ./setup.sh to fix"
