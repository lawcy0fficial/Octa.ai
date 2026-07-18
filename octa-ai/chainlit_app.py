"""
╔══════════════════════════════════════════════════════════════╗
║    Chainlit Chat UI v1.0 — Claude.ai-like Interface          ║
║    Full key rotation | Streaming | Memory | Vision           ║
║    Run: chainlit run chainlit_app.py                          ║
║    Access: http://localhost:8000                              ║
╚══════════════════════════════════════════════════════════════╝
"""

import chainlit as cl
import litellm
import os
import json
import base64
from itertools import cycle
from pathlib import Path
from datetime import datetime

# ── Load Keys ─────────────────────────────────────────────────
# Previously this duplicated bridge.py's bare open("keys.json"),
# which only works if chainlit happens to be launched from the exact
# folder containing keys.json — `chainlit run chainlit_app.py` from
# anywhere else silently loaded zero keys (bare except swallowed the
# error) and every model call 401'd, which is what showed up as
# "chainlit not working, showing error". Now it reuses keys.py's
# loader, which always finds keys.json next to itself.
import keys as _keys

OR_KEYS  = cycle(_keys._K.get("openrouter", []) or [""])
CB_KEYS  = cycle(_keys._K.get("cerebras",   []) or [""])
GK_KEYS  = cycle(_keys._K.get("grok",       []) or [""])
GM_KEYS  = cycle(_keys._K.get("gemini",     []) or [""])

# ── Model Pool ─────────────────────────────────────────────────
# OpenRouter free IDs come from the live fetch in keys.py, not a
# hardcoded (and partly dead) list.
_LIVE_OR_MODELS = _keys.fetch_openrouter_free_models(limit=5)
MODEL_POOL = cycle(
    [(f"openrouter/{m}", "openrouter") for m in _LIVE_OR_MODELS] + [
        ("cerebras/llama3.3-70b", "cerebras"),
        ("gemini/gemini-2.5-flash", "gemini"),
        ("xai/grok-beta", "grok"),
        ("ollama/phi3:mini", "ollama"),
    ]
)

def rotate_keys():
    os.environ["OPENROUTER_API_KEY"] = next(OR_KEYS)
    os.environ["CEREBRAS_API_KEY"]   = next(CB_KEYS)
    os.environ["XAI_API_KEY"]        = next(GK_KEYS)
    os.environ["GEMINI_API_KEY"]     = next(GM_KEYS)

rotate_keys()

SYSTEM = """You are an advanced personal AI research assistant
inspired by Claude.ai. You are helpful, intelligent, thorough,
and never incomplete in your answers. You can help with:
research, coding, security concepts, OSINT methodology,
data analysis, writing, and general assistance.
Always provide complete, detailed, and accurate responses."""

# ── Chat Start ─────────────────────────────────────────────────
@cl.on_chat_start
async def start():
    cl.user_session.set("history", [])
    cl.user_session.set("model",   next(MODEL_POOL))

    await cl.Message(content="""
👋 **Welcome to Your Personal OCTA AI v1.0!**

Powered by **82,500+ free API requests/day** across:
OpenRouter × Cerebras × Grok × Gemini × Ollama

**Commands:**
- `/model` — Switch AI model
- `/clear` — Clear conversation
- `/search [query]` — Web search
- `/cve [service] [version]` — CVE lookup
- `/image [prompt]` — Generate image
- `/capacity` — Show API capacity
- Type anything else to chat!

What can I help you with today? 🚀
""").send()

# ── Message Handler ────────────────────────────────────────────
@cl.on_message
async def main(message: cl.Message):
    history = cl.user_session.get("history", [])
    content = message.content.strip()
    rotate_keys()

    # ── Commands ───────────────────────────────────────────────
    if content.startswith("/model"):
        model, _ = next(MODEL_POOL)
        cl.user_session.set("model", (model, _))
        await cl.Message(f"✅ Switched to: `{model}`").send()
        return

    if content.startswith("/clear"):
        cl.user_session.set("history", [])
        await cl.Message("✅ Conversation cleared!").send()
        return

    if content.startswith("/capacity"):
        await cl.Message(content="""
## 📊 Free API Capacity

| Provider | Keys | Daily Limit |
|----------|------|------------|
| OpenRouter | 10 | 56,000 req/day |
| Cerebras | 9 | ~9M tokens/day |
| Grok/xAI | 9 | Large capacity |
| Gemini | 7 | 10,500 req/day |
| Requesty | 10 | 16,000 req/day |
| Ollama | ♾️ | Unlimited local |

**Total: ~82,500+ requests/day FREE** 🎉
""").send()
        return

    if content.startswith("/search "):
        query = content[8:].strip()
        thinking = await cl.Message("🔍 Searching...").send()
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    results.append(
                        f"**[{r.get('title')}]({r.get('href')})**\n"
                        f"{r.get('body', '')[:200]}\n"
                    )
            await cl.Message(
                f"## 🔍 Results for: {query}\n\n" +
                "\n".join(results)
            ).send()
        except Exception as e:
            await cl.Message(f"Search error: {e}").send()
        return

    if content.startswith("/cve "):
        parts   = content[5:].strip().split()
        service = parts[0] if parts else ""
        version = parts[1] if len(parts) > 1 else ""
        thinking = await cl.Message(
            f"🔬 Researching CVEs for {service} {version}...").send()
        try:
            import requests as req
            r = req.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0"
                f"?keywordSearch={service}+{version}&resultsPerPage=5",
                timeout=15)
            cves   = r.json().get("vulnerabilities", [])
            output = f"## 🔬 CVEs for {service} {version}\n\n"
            for v in cves[:5]:
                cve   = v.get("cve", {})
                score = (cve.get("metrics", {})
                        .get("cvssMetricV31", [{}])[0]
                        .get("cvssData", {})
                        .get("baseScore", "N/A"))
                desc  = (cve.get("descriptions", [{}])[0]
                        .get("value", ""))[:150]
                output += f"**{cve.get('id')}** (CVSS: {score})\n{desc}\n\n"
            await cl.Message(output).send()
        except Exception as e:
            await cl.Message(f"CVE error: {e}").send()
        return

    if content.startswith("/image "):
        prompt  = content[7:].strip()
        thinking = await cl.Message(
            f"🎨 Generating image: {prompt}...").send()
        try:
            import urllib.parse, requests as req
            ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
            Path("outputs").mkdir(exist_ok=True)
            encoded = urllib.parse.quote(prompt)
            url     = f"https://image.pollinations.ai/prompt/{encoded}?nologo=true"
            r       = req.get(url, timeout=60)
            if r.status_code == 200:
                img_path = f"outputs/image_{ts}.jpg"
                Path(img_path).write_bytes(r.content)
                elements = [cl.Image(path=img_path, name="Generated Image")]
                await cl.Message(
                    f"✅ Generated: {prompt}",
                    elements=elements
                ).send()
            else:
                await cl.Message(f"Error: HTTP {r.status_code}").send()
        except Exception as e:
            await cl.Message(f"Image error: {e}").send()
        return

    # ── Handle File Uploads ────────────────────────────────────
    extra_content = ""
    image_b64  = None
    image_mime = None
    IMAGE_MIME_MAP = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp",
    }
    if message.elements:
        for element in message.elements:
            if hasattr(element, 'path') and element.path:
                try:
                    ext = Path(element.path).suffix.lower()
                    if ext in IMAGE_MIME_MAP:
                        # Image analysis via Gemini
                        with open(element.path, "rb") as f:
                            image_b64 = base64.b64encode(
                                f.read()).decode()
                        image_mime = IMAGE_MIME_MAP[ext]
                        content = (
                            f"[Image uploaded: {element.name}]\n"
                            f"{content}"
                        )
                    else:
                        # Text file
                        text = Path(element.path).read_text(
                            errors='replace')
                        extra_content = (
                            f"\n\n**File: {element.name}**\n"
                            f"```\n{text[:3000]}\n```"
                        )
                except Exception:
                    pass

    # ── Build Messages ─────────────────────────────────────────
    messages = [{"role": "system", "content": SYSTEM}]

    # Last 10 conversation turns
    for turn in history[-10:]:
        messages.append(turn)

    # Current message
    if image_b64:
        messages.append({
            "role": "user",
            "content": [
                {"type": "image_url",
                 "image_url": {
                     "url": f"data:{image_mime};base64,{image_b64}"}},
                {"type": "text", "text": content}
            ]
        })
    else:
        user_content = content + extra_content
        messages.append({"role": "user", "content": user_content})

    # ── Stream Response ────────────────────────────────────────
    model_info = cl.user_session.get("model", next(MODEL_POOL))
    if isinstance(model_info, tuple):
        model, provider = model_info
    else:
        model, provider = model_info, "openrouter"

    response_msg  = cl.Message(content="")
    await response_msg.send()
    full_response = ""
    success       = False

    # Try current model + 5 fallbacks
    models_to_try = [(model, provider)] + [
        next(MODEL_POOL) for _ in range(6)]

    for try_model, try_provider in models_to_try:
        try:
            rotate_keys()
            kwargs = dict(
                model=try_model,
                messages=messages,
                stream=True,
                max_tokens=3000
            )
            if try_provider == "ollama":
                kwargs["api_base"] = "http://localhost:11434"

            response = litellm.completion(**kwargs)
            for chunk in response:
                token = chunk.choices[0].delta.content or ""
                if token:
                    await response_msg.stream_token(token)
                    full_response += token

            success = True
            cl.user_session.set("model", (try_model, try_provider))
            break

        except Exception as e:
            print(f"   ⚠️  {try_model}: {str(e)[:50]}")
            continue

    if not success:
        full_response = (
            "❌ All providers temporarily unavailable. "
            "Please try again in a moment.")
        await response_msg.stream_token(full_response)

    await response_msg.update()

    # Save to history
    history.append({"role": "user",      "content": content})
    history.append({"role": "assistant", "content": full_response})
    cl.user_session.set("history", history[-20:])

    # Save to memory
    try:
        from memory import save_conversation
        save_conversation(content, full_response)
    except Exception:
        pass

if __name__ == "__main__":
    print("Run: chainlit run chainlit_app.py")
    print("Access: http://localhost:8000")
