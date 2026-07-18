"""
╔══════════════════════════════════════════════════════════════╗
║    FastAPI Bridge v1.0 — Full Provider Rotation              ║
║    Connects Open WebUI to all free API providers             ║
║    Run: python3 bridge.py                                 ║
║    Open WebUI: http://localhost:3000                         ║
╚══════════════════════════════════════════════════════════════╝
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import litellm
import uvicorn
import json
import time
import os
from itertools import cycle
from pathlib import Path

# ── Load Keys ─────────────────────────────────────────────────
# This used to open("keys.json") relative to the CURRENT WORKING
# DIRECTORY with a bare `except: return {}`. If bridge.py was ever
# launched from anywhere other than the folder containing keys.json
# (e.g. via start_all.sh, a systemd unit, or Open WebUI's own cwd),
# it silently loaded ZERO keys and every provider call 401'd — which
# is what "added localhost:8001 but it's not accessing api from
# key.json" actually was. Now it imports the shared loader in
# keys.py, which always finds keys.json next to itself regardless
# of cwd, and reuses the SAME rotation logic as every other module.
import keys as _keys

OR_KEYS  = cycle(_keys._K.get("openrouter", []) or [""])
CB_KEYS  = cycle(_keys._K.get("cerebras",   []) or [""])
GK_KEYS  = cycle(_keys._K.get("grok",       []) or [""])
GM_KEYS  = cycle(_keys._K.get("gemini",     []) or [""])
RQ_KEYS  = cycle(_keys._K.get("requesty",   []) or [""])
NV_KEYS  = cycle(_keys._K.get("novita",     []) or [""])

def rotate():
    os.environ["OPENROUTER_API_KEY"] = next(OR_KEYS)
    os.environ["CEREBRAS_API_KEY"]   = next(CB_KEYS)
    os.environ["XAI_API_KEY"]        = next(GK_KEYS)
    os.environ["GEMINI_API_KEY"]     = next(GM_KEYS)

rotate()

# ── All Models ─────────────────────────────────────────────────
# OpenRouter free-model IDs are pulled live (see keys.py) instead of
# hardcoded, since OpenRouter rotates its free lineup and several of
# the old hardcoded IDs here no longer exist (e.g. there was never a
# free Claude 3 Haiku on OpenRouter, and DeepSeek/Mistral pulled all
# their free variants in mid-2026). Hardcoded stale IDs were exactly
# why the model dropdown "worked" but every actual reply failed.
_LIVE_OR_MODELS = _keys.fetch_openrouter_free_models(limit=6)

ALL_MODELS = [
    ("cerebras/llama3.3-70b",
     "cerebras", "cerebras-fast",
     "⚡ Cerebras LLaMA 3.3 70B (2000 tok/s)"),

    ("gemini/gemini-2.5-flash",
     "gemini", "gemini-flash",
     "✨ Gemini 2.5 Flash — 1M Context"),

    ("xai/grok-beta",
     "grok", "grok-beta",
     "🌟 Grok Beta — xAI Model"),

    ("ollama/phi3:mini",
     "ollama", "ollama-phi3",
     "💻 Ollama phi3:mini — Local Unlimited"),

    ("ollama/qwen2.5:3b",
     "ollama", "ollama-qwen",
     "💻 Ollama Qwen 2.5 3B — Local Unlimited"),
] + [
    (f"openrouter/{m}", "openrouter",
     "or-" + m.split("/")[-1].replace(":free", ""),
     f"🌐 {m} (Free, live from OpenRouter)")
    for m in _LIVE_OR_MODELS
]

MODEL_ID_MAP = {m[2]: (m[0], m[1]) for m in ALL_MODELS}
MODEL_CYCLE  = cycle([(m[0], m[1]) for m in ALL_MODELS])

# ── App ────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Agent Bridge v1.0",
    description="Full rotation across all free providers",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models Endpoint ────────────────────────────────────────────
@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id":       m[2],
                "object":   "model",
                "owned_by": m[1],
                "description": m[3]
            }
            for m in ALL_MODELS
        ]
    }

# ── Chat Completions ───────────────────────────────────────────
@app.post("/v1/chat/completions")
async def chat(request: dict):
    messages   = request.get("messages", [])
    stream     = request.get("stream", False)
    model_req  = request.get("model", "auto")
    max_tokens = request.get("max_tokens", 2000)

    # Select model
    if model_req in MODEL_ID_MAP:
        model, provider = MODEL_ID_MAP[model_req]
    elif model_req == "auto":
        model, provider = next(MODEL_CYCLE)
    else:
        model, provider = next(MODEL_CYCLE)

    rotate()

    async def try_models(stream_mode: bool):
        """Try models with fallback."""
        tried = [(model, provider)]
        for _ in range(8):
            for m, p in tried[-1:]:
                try:
                    kwargs = dict(
                        model=m,
                        messages=messages,
                        max_tokens=max_tokens,
                        stream=stream_mode
                    )
                    if p == "ollama":
                        kwargs["api_base"] = "http://localhost:11434"
                    elif p == "requesty":
                        kwargs["api_base"] = "https://router.requesty.ai/v1"
                        kwargs["api_key"]  = next(RQ_KEYS)
                    elif p == "novita":
                        kwargs["api_base"] = "https://api.novita.ai/v3/openai"
                        kwargs["api_key"]  = next(NV_KEYS)

                    return litellm.completion(**kwargs), m, p

                except Exception as e:
                    print(f"   ⚠️  {m}: {str(e)[:50]}")
                    rotate()
                    next_m, next_p = next(MODEL_CYCLE)
                    tried.append((next_m, next_p))
                    time.sleep(0.5)

        return None, None, None

    # Streaming
    if stream:
        async def generate():
            response, used_m, used_p = await try_models(True)
            if not response:
                yield f"data: {json.dumps({'error': 'All providers failed'})}\n\n"
                return
            try:
                for chunk in response:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        data = {
                            "id":     "chat-stream",
                            "object": "chat.completion.chunk",
                            "choices": [{
                                "delta":         {"content": delta.content},
                                "index":         0,
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )

    # Non-streaming
    response, _, _ = await try_models(False)
    if response:
        return response
    return {"error": "All providers failed",
            "choices": [{"message": {
                "content": "Service temporarily unavailable.",
                "role": "assistant"
            }}]}

# ── Status Endpoints ───────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name":    "AI Agent Bridge v1.0",
        "status":  "running",
        "webui":   "http://localhost:3000",
        "docs":    "http://localhost:8001/docs",
        "models":  len(ALL_MODELS),
        "tip":     "In Open WebUI: Settings → Connections → Add http://localhost:8001"
    }

@app.get("/health")
async def health():
    return {
        "status":  "ok",
        "version": "1.0",
        "providers": {
            "openrouter": f"10 keys",
            "cerebras":   f"9 keys",
            "grok":       f"9 keys",
            "gemini":     f"7 keys",
            "requesty":   f"10 keys",
            "novita":     f"8 keys",
            "ollama":     "unlimited local"
        },
        "total_capacity": "82,500+ req/day"
    }

# ── Run ────────────────────────────────────────────────────────
if __name__ == "__main__":
    model_lines = "\n".join(
        f"║  - {m[2]:<28} {m[3][:33]:<33} ║" for m in ALL_MODELS
    )
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          AI Agent Bridge v1.0 — All Providers               ║
╠══════════════════════════════════════════════════════════════╣
║  Bridge URL:  http://localhost:8001                          ║
║  API Docs:    http://localhost:8001/docs                     ║
║  Open WebUI:  http://localhost:3000                          ║
╠══════════════════════════════════════════════════════════════╣
║  In Open WebUI (Docker):                                     ║
║  Settings → Connections → Add: http://host.docker.internal:8001/v1
╠══════════════════════════════════════════════════════════════╣
║  Models Available (live at startup):                         ║
{model_lines}
╚══════════════════════════════════════════════════════════════╝
""")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
