"""
╔══════════════════════════════════════════════════════════════╗
║   Shared Keys & Provider Module — v1.0                       ║
║   Imported by ALL modules for unified key rotation           ║
║   DO NOT run directly — import this module                   ║
╚══════════════════════════════════════════════════════════════╝

Usage in any module:
    from keys import call_ai, call_local, rotate, POOLS
"""

import os
import json
import time
import litellm
from itertools import cycle
from pathlib import Path
from typing import Tuple, Optional

litellm.set_verbose = False

# ══════════════════════════════════════════════════════════════
# LOAD KEYS FROM keys.json
# ══════════════════════════════════════════════════════════════
#
# IMPORTANT: the FIRST location checked is always the one next to
# THIS file (keys.py), not the current working directory. That's
# what makes key-loading work no matter where a script is launched
# from (chainlit run, uvicorn, systemd, a cron job with a different
# cwd, etc). The cwd-relative paths are kept only as a convenience
# fallback for ad-hoc `python3 keys.py` testing.

def _load_keys() -> dict:
    """Load keys from keys.json — searches multiple locations."""
    locations = [
        str(Path(__file__).resolve().parent / "keys.json"),
        "keys.json",
        "../keys.json",
        str(Path.home() / "agent" / "keys.json"),
    ]
    for loc in locations:
        if Path(loc).exists():
            try:
                with open(loc) as f:
                    data = json.load(f)
                    print(f"   🔑 Keys loaded from: {loc}")
                    return data
            except Exception as e:
                print(f"   ⚠️  Could not load {loc}: {e}")
    print("   ⚠️  No keys.json found in any known location — "
          "every provider call will fail auth until you fix this.")
    return {}

_K = _load_keys()

# ══════════════════════════════════════════════════════════════
# KEY POOLS — All providers cycling
# ══════════════════════════════════════════════════════════════

# NOTE: no hardcoded fallback keys — populate keys.json instead.
OR_KEYS = cycle(_K.get("openrouter", []) or [""])
CB_KEYS = cycle(_K.get("cerebras", []) or [""])
GK_KEYS = cycle(_K.get("grok", []) or [""])
GM_KEYS = cycle(_K.get("gemini", []) or [""])
RQ_KEYS = cycle(_K.get("requesty", []) or [""])
NV_KEYS = cycle(_K.get("novita", []) or [""])

HF_KEY    = (_K.get("huggingface", []) or [""])[0]
POLL_KEY  = (_K.get("pollinations", []) or [""])[0]
CF_KEY    = (_K.get("cloudflare", []) or [""])[0]

# ══════════════════════════════════════════════════════════════
# KEY ROTATION — Sets env vars before each call
# ══════════════════════════════════════════════════════════════

def rotate():
    """Rotate all provider keys in environment."""
    os.environ["OPENROUTER_API_KEY"] = next(OR_KEYS)
    os.environ["CEREBRAS_API_KEY"]   = next(CB_KEYS)
    os.environ["XAI_API_KEY"]        = next(GK_KEYS)
    os.environ["GEMINI_API_KEY"]     = next(GM_KEYS)
    os.environ["HF_TOKEN"]           = HF_KEY

# Set initial keys on import
rotate()

# ══════════════════════════════════════════════════════════════
# LIVE OPENROUTER FREE-MODEL DISCOVERY
# ══════════════════════════════════════════════════════════════
#
# OpenRouter's free (":free") model lineup rotates constantly —
# providers add/remove free slugs with no notice, and a slug that
# was free last month can silently 400/404 today. Hardcoding a
# fixed list of :free IDs is why "auto-selecting a free model" was
# breaking: half the IDs baked into this file were already dead.
# This fetches the CURRENT free roster straight from OpenRouter at
# startup, with the old hardcoded list kept only as an offline
# fallback if the fetch fails (e.g. no internet yet).

import requests as _requests

_FREE_MODEL_CACHE_FILE = Path(__file__).resolve().parent / ".free_models_cache.json"

_FALLBACK_FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-235b-a22b:free",
    "google/gemma-3-12b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]

def fetch_openrouter_free_models(limit: int = 8, max_age_hours: int = 6) -> list:
    """
    Return up to `limit` currently-free OpenRouter model IDs
    (bare id, e.g. 'meta-llama/llama-3.3-70b-instruct:free').
    Caches the result on disk for `max_age_hours` so we don't hit
    the models endpoint on every single process start.
    """
    try:
        if _FREE_MODEL_CACHE_FILE.exists():
            age = time.time() - _FREE_MODEL_CACHE_FILE.stat().st_mtime
            if age < max_age_hours * 3600:
                cached = json.loads(_FREE_MODEL_CACHE_FILE.read_text())
                if cached:
                    return cached[:limit]
    except Exception:
        pass

    try:
        r = _requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        r.raise_for_status()
        ids = [m["id"] for m in r.json().get("data", []) if m.get("id", "").endswith(":free")]
        if ids:
            try:
                _FREE_MODEL_CACHE_FILE.write_text(json.dumps(ids))
            except Exception:
                pass
            print(f"   🌐 Fetched {len(ids)} live free OpenRouter models")
            return ids[:limit]
    except Exception as e:
        print(f"   ⚠️  Could not fetch live OpenRouter model list ({e}) — using offline fallback")

    return _FALLBACK_FREE_MODELS[:limit]


_LIVE_FREE = fetch_openrouter_free_models(limit=6)

# ══════════════════════════════════════════════════════════════
# MODEL POOLS — Shared across all modules
# ══════════════════════════════════════════════════════════════

# All online providers — best quality + speed.
# OpenRouter entries are built from the LIVE free list above, so
# this pool never gets stuck on a dead :free slug.
ONLINE_POOL = cycle(
    [(f"openrouter/{m}", "openrouter") for m in _LIVE_FREE] + [
        ("cerebras/llama3.3-70b", "cerebras"),
        ("gemini/gemini-2.5-flash", "gemini"),
        ("xai/grok-beta", "grok"),
    ]
)

# Discussion — best reasoning models
DISCUSSION_POOL = cycle(
    [(f"openrouter/{m}", "openrouter") for m in _LIVE_FREE] + [
        ("gemini/gemini-2.5-flash", "gemini"),
        ("xai/grok-beta", "grok"),
        ("cerebras/llama3.3-70b", "cerebras"),
    ]
)

# Planning — fastest models
PLANNING_POOL = cycle(
    [
        ("cerebras/llama3.3-70b", "cerebras"),
        ("gemini/gemini-2.5-flash", "gemini"),
        ("xai/grok-beta", "grok"),
    ] + [(f"openrouter/{m}", "openrouter") for m in _LIVE_FREE]
)

# Execution — LOCAL ONLY (unlimited, no filters)
EXECUTION_POOL = cycle([
    ("ollama/phi3:mini",    "ollama"),
    ("ollama/qwen2.5:3b",   "ollama"),
    ("ollama/llama3.2:3b",  "ollama"),
])

# Review — best quality
REVIEW_POOL = cycle(
    [(f"openrouter/{m}", "openrouter") for m in _LIVE_FREE] + [
        ("gemini/gemini-2.5-flash", "gemini"),
        ("cerebras/llama3.3-70b", "cerebras"),
        ("xai/grok-beta", "grok"),
    ]
)

# Vision — Gemini only (has vision capability)
VISION_POOL = cycle([
    ("gemini/gemini-2.5-flash", "gemini"),
])

# All pools dict for easy access
POOLS = {
    "online":     ONLINE_POOL,
    "discussion": DISCUSSION_POOL,
    "planning":   PLANNING_POOL,
    "execution":  EXECUTION_POOL,
    "review":     REVIEW_POOL,
    "vision":     VISION_POOL,
}

# ══════════════════════════════════════════════════════════════
# CORE AI CALL — Used by ALL modules
# ══════════════════════════════════════════════════════════════

def call_ai(messages: list,
            pool=None,
            label: str = "",
            retries: int = 12,
            max_tokens: int = 4000) -> Tuple[str, str]:
    """
    Universal AI caller — shared by all modules.
    Full provider + key rotation with auto-fallback.
    Returns: (response_text, model_used)
    """
    if pool is None:
        pool = ONLINE_POOL

    for attempt in range(retries):
        model, provider = next(pool)
        rotate()

        try:
            icon = "▶" if attempt == 0 else "🔁"
            print(f"   {icon} [{label}] {model[:50]}")

            kwargs = dict(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                timeout=45
            )

            if provider == "ollama":
                kwargs["api_base"] = "http://localhost:11434"
            elif provider == "requesty":
                kwargs["api_base"] = "https://router.requesty.ai/v1"
                kwargs["api_key"]  = next(RQ_KEYS)
            elif provider == "novita":
                kwargs["api_base"] = "https://api.novita.ai/v3/openai"
                kwargs["api_key"]  = next(NV_KEYS)

            response = litellm.completion(**kwargs)
            result   = response.choices[0].message.content
            print(f"   ✅ [{label}] ← {model[:40]}")
            return result, model

        except Exception as e:
            err = str(e)[:70]
            if "429" in err or "rate" in err.lower():
                print(f"   ⏳ Rate limit → rotating...")
            elif "401" in err or "auth" in err.lower():
                print(f"   🔑 Auth error → rotating key...")
            else:
                print(f"   ⚠️  {err[:50]}")
            time.sleep(1)

    return "ERROR: All providers failed.", "none"


def call_local(messages: list,
               label: str = "",
               max_tokens: int = 4000) -> Tuple[str, str]:
    """
    Call LOCAL Ollama only — unlimited, no filters, private.
    Used for execution phase and security research.
    """
    return call_ai(messages, EXECUTION_POOL, label, max_tokens=max_tokens)


def call_fast(messages: list,
              label: str = "",
              max_tokens: int = 2000) -> Tuple[str, str]:
    """Call fastest providers — Cerebras first."""
    return call_ai(messages, PLANNING_POOL, label, max_tokens=max_tokens)


def call_vision(image_path: str,
                question: str = "Describe this image.") -> str:
    """Analyze image using Gemini vision (rotates keys)."""
    import base64
    try:
        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()

        ext  = image_path.rsplit(".", 1)[-1].lower()
        mime = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png",  "gif":  "image/gif",
            "webp":"image/webp", "bmp":  "image/bmp",
        }.get(ext, "image/jpeg")

        rotate()
        os.environ["GEMINI_API_KEY"] = next(GM_KEYS)

        response = litellm.completion(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": [
                {"type": "image_url",
                 "image_url": {
                     "url": f"data:{mime};base64,{img_data}"}},
                {"type": "text", "text": question}
            ]}],
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Vision error: {e}"


def call_stream(messages: list,
                label: str = "") -> str:
    """Stream response word by word."""
    model, provider = next(DISCUSSION_POOL)
    rotate()
    try:
        kwargs = dict(
            model=model, messages=messages,
            stream=True, max_tokens=3000)
        if provider == "ollama":
            kwargs["api_base"] = "http://localhost:11434"

        response = litellm.completion(**kwargs)
        full = ""
        for chunk in response:
            token = chunk.choices[0].delta.content or ""
            if token:
                print(token, end="", flush=True)
                full += token
        print()
        return full
    except Exception as e:
        result, _ = call_ai(messages, ONLINE_POOL, label)
        return result


# ══════════════════════════════════════════════════════════════
# CAPACITY INFO
# ══════════════════════════════════════════════════════════════

def get_capacity() -> str:
    """Return formatted capacity string."""
    return """
╔══════════════════════════════════════════════════════════════╗
║         TYPICAL FREE-TIER CAPACITY PER KEY — v1.0            ║
║   (add your own keys to keys.json — none ship by default)    ║
╠══════════════════════════════════════════════════════════════╣
║  Provider      Per-key daily limit         Speed              ║
║  ──────────────────────────────────────────────────────────  ║
║  OpenRouter    ~200 req × free models       Varies            ║
║  Cerebras      ~1M tokens/day              ⚡ 2,000 tok/s    ║
║  Grok/xAI      Provider-set free tier       Fast              ║
║  Gemini        ~1,500 req/day               Fast (1M ctx)    ║
║  Requesty      ~200 req/day                 Fast              ║
║  Novita        Free tier                    Fast              ║
║  HuggingFace   ~2,000 req/day               Moderate          ║
║  Ollama        ♾️  UNLIMITED local          RAM dependent     ║
╠══════════════════════════════════════════════════════════════╣
║  Add more keys per provider in keys.json to rotate through   ║
║  more free-tier quota. Ollama alone needs zero cloud keys.   ║
║  COST:         $0/month                                      ║
╚══════════════════════════════════════════════════════════════╝"""


# ══════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🔑 Keys module test...")
    print(get_capacity())
    print("\nTesting call_ai...")
    result, model = call_ai(
        [{"role": "user", "content": "Say hello in one word."}],
        ONLINE_POOL, "test", max_tokens=10
    )
    print(f"Response: {result}")
    print(f"Model: {model}")
