#!/bin/bash
echo "⏹️  Stopping components..."
pkill -f "bridge.py"       2>/dev/null && echo "   ✅ Bridge"
pkill -f "mcp_master.py"   2>/dev/null && echo "   ✅ MCP"
pkill -f "chainlit_app.py" 2>/dev/null && echo "   ✅ Chainlit"
pkill -f "agent.py"        2>/dev/null && echo "   ✅ Agent"
echo "Done! (Ollama still running — stop with: pkill ollama)"
