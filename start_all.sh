#!/bin/bash
# Start all agent components
echo "🚀 Starting OCTA AI v1.0..."
cd ~/agent 2>/dev/null || cd "$(dirname "$0")"

echo "   [1/4] Ollama..."
pgrep -x ollama > /dev/null || (ollama serve &>/dev/null & sleep 3)
echo "   ✅ Ollama"

echo "   [2/4] MCP..."
pgrep -f mcp_master.py > /dev/null || (python3 mcp_master.py &>/dev/null &)
sleep 1
echo "   ✅ MCP"

echo "   [3/4] Bridge..."
lsof -i:8001 > /dev/null 2>&1 || (python3 bridge.py &>/dev/null & sleep 2)
echo "   ✅ Bridge (port 8001)"

echo "   [4/4] Open WebUI..."
docker ps 2>/dev/null | grep -q open-webui || \
  docker run -d -p 3000:8080 -v open-webui:/app/backend/data \
  --add-host=host.docker.internal:host-gateway \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:main &>/dev/null
echo "   ✅ Open WebUI"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ ALL STARTED                          ║"
echo "║  Open WebUI:  http://localhost:3000      ║"
echo "║  Bridge:      http://localhost:8001      ║"
echo "║  CLI Agent:   python3 agent.py           ║"
echo "║  Chat UI:     chainlit run chainlit_app.py║"
echo "║  Security:    python3 security_agent.py  ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "In Open WebUI: Settings → Connections → http://host.docker.internal:8001"
echo "(NOT localhost:8001 — Open WebUI runs in its own container, so"
echo "'localhost' there means the container, not this machine)"
