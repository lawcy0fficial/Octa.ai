#!/usr/bin/env python3
"""
Claude Code Setup
==================
Wires up Claude Code to talk to REAL Claude models.

IMPORTANT — why the old version of this file didn't work:
Claude Code's ANTHROPIC_BASE_URL expects the Anthropic-native
Messages API. OpenRouter serves an OpenAI-compatible
`/v1/chat/completions` shape instead, and OpenRouter has never
listed a free Claude model (Anthropic doesn't offer free-tier
models on OpenRouter or anywhere else). So the old script's plan —
route Claude Code through OpenRouter, aim it at
"anthropic/claude-3-haiku:free" or a Llama model and call it
Claude — could never work: wrong protocol AND a model ID that
doesn't exist. There is no free way to get real Claude in an
agentic coding loop; use one of the two supported paths below.

Usage: python3 claude_code_setup.py
"""

import json
import subprocess
from pathlib import Path


def _load_keys() -> dict:
    for loc in ("keys.json", str(Path(__file__).parent / "keys.json")):
        p = Path(loc)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
    return {}


def setup_claude_code():
    """
    Configure Claude Code the two ways that actually work:

    1) Subscription login (recommended, no API key needed):
         claude
       then follow the browser login prompt. Uses your Claude
       Pro/Max plan quota.

    2) Pay-as-you-go API key from console.anthropic.com (put it in
       keys.json under "anthropic": ["sk-ant-..."] ), which this
       script will wire into ~/.claude/settings.json.
    """
    keys = _load_keys()
    anthropic_keys = keys.get("anthropic", [])

    config_path = Path.home() / ".claude" / "settings.json"
    config_path.parent.mkdir(exist_ok=True)

    if anthropic_keys and anthropic_keys[0]:
        config = {
            "env": {"ANTHROPIC_API_KEY": anthropic_keys[0]},
            "model": "claude-sonnet-4-6",
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(Path.home())]
                },
                "fetch": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-fetch"]
                },
                "parrot-master": {
                    "command": "python3",
                    "args": [str(Path.home() / "agent/mcp_master.py")]
                }
            }
        }
        config_path.write_text(json.dumps(config, indent=2))
        print("✅ ~/.claude/settings.json written using your Anthropic API key.")
        print("   Run: claude")
    else:
        # No API key on file — set up MCP servers only, and point the
        # person at subscription login instead of a broken free route.
        config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(Path.home())]
                },
                "fetch": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-fetch"]
                },
                "parrot-master": {
                    "command": "python3",
                    "args": [str(Path.home() / "agent/mcp_master.py")]
                }
            }
        }
        config_path.write_text(json.dumps(config, indent=2))
        print("ℹ️  No anthropic key found in keys.json.")
        print("   MCP servers are configured; for the model itself, either:")
        print("     • run `claude` and log in with your Claude subscription, or")
        print("     • add a real key to keys.json under \"anthropic\": [\"sk-ant-...\"]")
        print("       from https://console.anthropic.com/settings/keys")

    return config


def show_ollama_status():
    """Check Ollama models available (for the LOCAL execution pool, unrelated to Claude Code)."""
    try:
        result = subprocess.run("ollama list", shell=True, capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            print("\n🤖 Ollama Models Available:")
            print(result.stdout)
        else:
            print("\n⚠️  No Ollama models found — run: ollama pull phi3:mini")
    except Exception:
        print("\n⚠️  Ollama not running — run: ollama serve")


if __name__ == "__main__":
    setup_claude_code()
    show_ollama_status()
