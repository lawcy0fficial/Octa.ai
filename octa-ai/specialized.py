"""
Specialized Capabilities v1.0 — Fully Connected
=================================================
Image Gen | Voice | Data Analysis | Code Execution
Imports: keys.py, memory.py, outputs.py
"""

import os, subprocess, json, requests
import urllib.parse
from datetime import datetime
from pathlib import Path

# ── Import shared modules ─────────────────────────────────────
from keys   import call_ai, call_fast, GM_KEYS, ONLINE_POOL, rotate
from memory import save_research, save_task
from outputs import save_all_formats

# ══════════════════════════════════════════════════════════════
# IMAGE GENERATION — Pollinations.ai (100% Free, No Key)
# ══════════════════════════════════════════════════════════════

def generate_image(prompt: str,
                   filename: str = None,
                   width: int = 1024,
                   height: int = 1024,
                   model: str = "flux") -> str:
    """
    Generate image via Pollinations.ai — 100% free, no key!
    Auto-saves and stores in memory.
    """
    if not filename:
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"outputs/image_{ts}.jpg"

    Path("outputs").mkdir(exist_ok=True)

    encoded = urllib.parse.quote(prompt)
    url     = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}"
        f"&model={model}&nologo=true&seed={hash(prompt) % 9999}"
    )

    print(f"   🎨 Generating: {prompt[:60]}...")
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            Path(filename).write_bytes(r.content)
            print(f"   ✅ Saved: {filename}")
            # Save to memory
            save_research(
                f"Image: {prompt[:50]}",
                f"Generated image saved to {filename}",
                tags=["image", "generated"]
            )
            return filename
        return f"Error: HTTP {r.status_code}"
    except Exception as e:
        return f"Error: {e}"

def generate_diagram(description: str,
                     filename: str = None) -> str:
    """Generate technical diagram."""
    prompt = (
        "Technical diagram, clean professional style, "
        "white background, clear labels, high detail: "
        f"{description}"
    )
    return generate_image(prompt, filename, 1200, 800)

def generate_report_cover(title: str,
                           filename: str = None) -> str:
    """Generate professional report cover image."""
    prompt = (
        "Professional cybersecurity report cover, "
        "dark theme, blue accents, tech aesthetic, "
        f"title text: {title}"
    )
    return generate_image(prompt, filename, 800, 1100)

# ══════════════════════════════════════════════════════════════
# VISION — Image Analysis (Gemini Free, Key Rotation)
# ══════════════════════════════════════════════════════════════

def analyze_image(image_path: str,
                  question: str = "Describe this image in detail.",
                  context: str = "general") -> str:
    """
    Analyze image using Gemini vision (rotates keys).
    Saves analysis to memory.
    """
    import base64

    # Context-specific prompts
    prompts = {
        "security": (
            "Analyze for security issues: exposed credentials, "
            "error messages, misconfigs, sensitive data, "
            "attack surfaces visible."
        ),
        "code": (
            "Analyze the code shown: language, purpose, "
            "bugs, security issues, improvements."
        ),
        "network": (
            "Analyze network diagram/capture: topology, "
            "protocols, anomalies, security concerns."
        ),
        "forensics": (
            "Extract all evidence from this image: "
            "text, metadata, artifacts, timestamps, anomalies."
        ),
        "general": question,
    }
    final_question = prompts.get(context, question)

    try:
        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()

        ext  = image_path.rsplit(".", 1)[-1].lower()
        mime = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png",  "gif":  "image/gif",
            "webp":"image/webp", "bmp":  "image/bmp",
        }.get(ext, "image/jpeg")

        # Rotate Gemini key
        rotate()
        import litellm
        response = litellm.completion(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": [
                {"type": "image_url",
                 "image_url": {
                     "url": f"data:{mime};base64,{img_data}"}},
                {"type": "text", "text": final_question}
            ]}],
            max_tokens=2000
        )
        result = response.choices[0].message.content

        # Save analysis to memory
        save_research(
            f"Vision: {image_path}",
            result[:500],
            tags=["vision", context, image_path]
        )
        return result

    except Exception as e:
        return f"Vision error: {e}"

def extract_text_from_image(image_path: str) -> str:
    """Extract all text from image (OCR via AI)."""
    return analyze_image(
        image_path,
        "Extract ALL text visible in this image exactly. "
        "Preserve formatting and line breaks. "
        "Return ONLY the text content."
    )

def analyze_screenshot(path: str,
                        context: str = "security") -> str:
    """Analyze screenshot for specific context."""
    return analyze_image(path, context=context)

# ══════════════════════════════════════════════════════════════
# VOICE / TTS — Coqui TTS (Free, Local)
# ══════════════════════════════════════════════════════════════

def text_to_speech(text: str,
                   output: str = None,
                   play: bool = False) -> str:
    """
    Convert text to speech using Coqui TTS (free, local).
    Optionally plays audio immediately.
    """
    if not output:
        ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"outputs/speech_{ts}.wav"

    Path("outputs").mkdir(exist_ok=True)

    # Check if tts installed
    import shutil
    if not shutil.which("tts"):
        print("   📦 Installing Coqui TTS...")
        subprocess.run(
            "pip3 install TTS --break-system-packages",
            shell=True, capture_output=True)

    print(f"   🔊 Converting to speech...")
    safe_text = text[:500].replace('"', "'").replace("'", "")
    result    = subprocess.run(
        f'tts --text "{safe_text}" --out_path {output}',
        shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"   ✅ Audio: {output}")
        if play:
            _play_audio(output)
        return output
    return f"TTS error: {result.stderr[:100]}"

def _play_audio(filepath: str):
    """Play audio file."""
    for player in ["aplay", "mpg123", "ffplay -nodisp -autoexit"]:
        r = subprocess.run(
            f"{player} {filepath}",
            shell=True, capture_output=True)
        if r.returncode == 0:
            return
    print("   ⚠️  No audio player found")

def speak(text: str) -> str:
    """Generate speech and play it."""
    audio = text_to_speech(text)
    if not audio.startswith("Error"):
        _play_audio(audio)
    return audio

# ══════════════════════════════════════════════════════════════
# DATA ANALYSIS — Pandas + AI
# ══════════════════════════════════════════════════════════════

def analyze_csv(filepath: str,
                question: str = None) -> dict:
    """
    AI-powered CSV data analysis.
    Uses shared keys module for AI calls.
    """
    try:
        import pandas as pd

        df      = pd.read_csv(filepath)
        numeric = df.select_dtypes(include=["number"]).columns

        summary = {
            "file":    filepath,
            "rows":    df.shape[0],
            "cols":    df.shape[1],
            "columns": list(df.columns),
            "dtypes":  {k: str(v) for k, v in df.dtypes.items()},
            "missing": df.isnull().sum().to_dict(),
            "sample":  df.head(5).to_dict(),
        }
        if len(numeric) > 0:
            summary["stats"] = df[numeric].describe().to_dict()

        prompt = (question if question else
                  "Analyze this dataset and provide: "
                  "1) Key insights and patterns "
                  "2) Notable statistics "
                  "3) Anomalies or concerns "
                  "4) Recommended next steps")

        combined = json.dumps(summary, indent=2,
                              default=str)[:4000]
        analysis, model = call_ai(
            [{"role": "system", "content":
                "Expert data analyst. Be specific and insightful."},
             {"role": "user", "content":
                f"Query: {prompt}\n\nData:\n{combined}"}],
            ONLINE_POOL, label="data-analysis"
        )
        summary["ai_analysis"] = analysis
        summary["model_used"]  = model

        # Save to memory
        save_research(
            f"Data Analysis: {filepath}",
            analysis[:500],
            tags=["data", "csv", filepath]
        )
        return summary

    except ImportError:
        subprocess.run(
            "pip3 install pandas --break-system-packages",
            shell=True, capture_output=True)
        return analyze_csv(filepath, question)
    except Exception as e:
        return {"error": str(e)}

def create_chart(data: dict,
                 chart_type: str = "bar",
                 title: str = "Chart",
                 filename: str = None) -> str:
    """Create chart from data dict."""
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        matplotlib.use("Agg")

        if not filename:
            ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"outputs/chart_{ts}.png"
        Path("outputs").mkdir(exist_ok=True)

        fig, ax = plt.subplots(figsize=(12, 6))
        keys    = list(data.keys())
        values  = list(data.values())

        if chart_type == "bar":
            ax.bar(keys, values, color="#0080ff", alpha=0.8)
        elif chart_type == "line":
            ax.plot(keys, values, marker="o",
                    color="#0080ff", linewidth=2)
        elif chart_type == "pie":
            ax.pie(values, labels=keys, autopct="%1.1f%%",
                   startangle=90)
        elif chart_type == "scatter":
            ax.scatter(range(len(keys)), values,
                       color="#0080ff", s=100)
            ax.set_xticks(range(len(keys)))
            ax.set_xticklabels(keys, rotation=45)

        ax.set_title(title, fontsize=16, fontweight="bold",
                     color="#1a1a2e")
        plt.tight_layout()
        plt.savefig(filename, dpi=150,
                    bbox_inches="tight",
                    facecolor="white")
        plt.close()
        print(f"   ✅ Chart: {filename}")
        return filename

    except ImportError:
        subprocess.run(
            "pip3 install matplotlib --break-system-packages",
            shell=True, capture_output=True)
        return create_chart(data, chart_type, title, filename)
    except Exception as e:
        return f"Chart error: {e}"

def analyze_log(filepath: str,
                log_type: str = "general") -> dict:
    """AI-powered log file analysis."""
    try:
        with open(filepath, "r", errors="replace") as f:
            content = f.read()

        lines  = content.split("\n")
        total  = len(lines)
        sample = "\n".join(lines[:150])

        prompts = {
            "security": (
                "Analyze security log. Identify: "
                "attacks, suspicious IPs, failed auth, "
                "anomalies, incidents."
            ),
            "access": (
                "Analyze access log. Identify: "
                "unusual patterns, high-frequency requests, "
                "suspicious IPs, 4xx/5xx errors."
            ),
            "general": (
                "Analyze log file. Summarize: "
                "main events, errors, patterns, anomalies."
            ),
        }

        analysis, model = call_ai(
            [{"role": "system",
              "content": prompts.get(log_type, prompts["general"])},
             {"role": "user",
              "content":
                  f"Log: {filepath}\nLines: {total}\n\n"
                  f"Sample:\n{sample}"}],
            ONLINE_POOL, label="log-analysis"
        )

        result = {
            "file":     filepath,
            "lines":    total,
            "analysis": analysis,
            "model":    model
        }

        # Save to memory
        save_research(
            f"Log Analysis: {filepath}",
            analysis[:500],
            tags=["log", log_type, filepath]
        )
        return result

    except Exception as e:
        return {"error": str(e)}

# ══════════════════════════════════════════════════════════════
# LIVE CODE EXECUTION
# ══════════════════════════════════════════════════════════════

def run_python(code: str, timeout: int = 30) -> dict:
    """Execute Python code safely with timeout."""
    import tempfile
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py",
        delete=False, dir="/tmp"
    ) as f:
        f.write(code)
        tmp = f.name

    try:
        result = subprocess.run(
            ["python3", tmp],
            capture_output=True, text=True,
            timeout=timeout)

        output = {
            "success": result.returncode == 0,
            "stdout":  result.stdout,
            "stderr":  result.stderr,
            "code":    code[:200]
        }

        # Save task result
        save_task(
            f"Code execution: {code[:50]}",
            output["stdout"][:200] or output["stderr"][:200],
            "success" if output["success"] else "error"
        )
        return output

    except subprocess.TimeoutExpired:
        return {"success": False,
                "error": f"Timeout after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass

def run_bash(command: str, timeout: int = 30) -> dict:
    """Execute bash command safely."""
    try:
        result = subprocess.run(
            command, shell=True,
            capture_output=True, text=True,
            timeout=timeout)
        return {
            "success": result.returncode == 0,
            "stdout":  result.stdout,
            "stderr":  result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"success": False,
                "error": f"Timeout after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ══════════════════════════════════════════════════════════════
# MAIN TEST
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🛠️  Specialized Capabilities v1.0")
    print("─"*40)
    print("1. Generate image")
    print("2. Analyze image")
    print("3. Text to speech")
    print("4. Analyze CSV")
    print("5. Run Python code")

    choice = input("\nTest (1-5): ").strip()

    if choice == "1":
        p = input("Prompt: ")
        print(generate_image(p))
    elif choice == "2":
        p = input("Image path: ")
        q = input("Question [describe]: ") or "Describe this."
        print(analyze_image(p, q))
    elif choice == "3":
        t = input("Text: ")
        print(text_to_speech(t, play=True))
    elif choice == "4":
        p = input("CSV path: ")
        r = analyze_csv(p)
        print(r.get("ai_analysis", r))
    elif choice == "5":
        print("Enter Python code (blank line to run):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        print(run_python("\n".join(lines)))
