"""
Memory Module v1.0 — Persistent Agent Memory
==============================================
Uses ChromaDB for semantic memory across sessions.
Imported by: agent.py, security_agent.py, osint_agent.py,
             chainlit_app.py, websearch.py, specialized.py
"""

import chromadb
import hashlib
import json
from datetime import datetime
from pathlib import Path

# ── Initialize ChromaDB ───────────────────────────────────────
_client        = None
_conversations = None
_research      = None
_findings      = None
_tasks         = None
_available     = False

def init():
    """Initialize ChromaDB — call once at startup."""
    global _client, _conversations, _research
    global _findings, _tasks, _available

    try:
        Path("memory").mkdir(exist_ok=True)
        _client        = chromadb.PersistentClient(path="./memory")
        _conversations = _client.get_or_create_collection("conversations")
        _research      = _client.get_or_create_collection("research")
        _findings      = _client.get_or_create_collection("findings")
        _tasks         = _client.get_or_create_collection("tasks")
        _available     = True
        print("   🧠 Memory: ChromaDB initialized")
        return True
    except Exception as e:
        print(f"   ⚠️  Memory unavailable: {e}")
        _available = False
        return False

def _make_id(content: str) -> str:
    return hashlib.md5(
        f"{content}{datetime.now().isoformat()}".encode()
    ).hexdigest()

def _ensure_init():
    if not _available:
        init()

# ── Save Functions ────────────────────────────────────────────

def save_conversation(user_msg: str,
                      ai_response: str,
                      meta: dict = {}) -> bool:
    """Save conversation turn."""
    _ensure_init()
    if not _available or not _conversations:
        return False
    try:
        content = f"User: {user_msg}\nAI: {ai_response}"
        _conversations.add(
            documents=[content],
            metadatas=[{
                "ts":   datetime.now().isoformat(),
                "type": "conversation",
                **meta
            }],
            ids=[_make_id(content)]
        )
        return True
    except Exception:
        return False

def save_research(topic: str,
                  content: str,
                  tags: list = []) -> bool:
    """Save research finding."""
    _ensure_init()
    if not _available or not _research:
        return False
    try:
        _research.add(
            documents=[content],
            metadatas=[{
                "topic": topic,
                "ts":    datetime.now().isoformat(),
                "tags":  json.dumps(tags),
                "type":  "research"
            }],
            ids=[_make_id(f"{topic}{content}")]
        )
        return True
    except Exception:
        return False

def save_finding(target: str,
                 finding_type: str,
                 description: str,
                 severity: str = "info") -> bool:
    """Save security/research finding."""
    _ensure_init()
    if not _available or not _findings:
        return False
    try:
        content = (f"Target: {target}\n"
                   f"Type: {finding_type}\n"
                   f"{description}")
        _findings.add(
            documents=[content],
            metadatas=[{
                "target":   target,
                "type":     finding_type,
                "severity": severity,
                "ts":       datetime.now().isoformat()
            }],
            ids=[_make_id(content)]
        )
        return True
    except Exception:
        return False

def save_task(task: str,
              result: str,
              status: str = "complete") -> bool:
    """Save completed task."""
    _ensure_init()
    if not _available or not _tasks:
        return False
    try:
        content = f"Task: {task}\nResult: {result}"
        _tasks.add(
            documents=[content],
            metadatas=[{
                "task":   task[:100],
                "status": status,
                "ts":     datetime.now().isoformat()
            }],
            ids=[_make_id(content)]
        )
        return True
    except Exception:
        return False

def save_osint(target: str, data: dict) -> bool:
    """Save OSINT results."""
    return save_research(
        f"OSINT: {target}",
        json.dumps(data, default=str)[:3000],
        tags=["osint", target]
    )

def save_vuln(target: str, vuln_type: str,
              severity: str, details: str) -> bool:
    """Save vulnerability finding."""
    return save_finding(
        target, vuln_type, details, severity)

# ── Search Functions ──────────────────────────────────────────

def search(query: str,
           n: int = 5,
           collection: str = "all") -> list:
    """
    Semantic search across memory.
    Returns list of relevant past memories.
    """
    _ensure_init()
    if not _available:
        return []

    results  = []
    cols_map = {
        "conversations": _conversations,
        "research":      _research,
        "findings":      _findings,
        "tasks":         _tasks,
    }

    cols = (cols_map if collection == "all"
            else {collection: cols_map.get(collection)})

    for name, col in cols.items():
        if not col:
            continue
        try:
            res  = col.query(query_texts=[query],
                             n_results=min(n, 3))
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            for doc, meta in zip(docs, metas):
                results.append({
                    "collection": name,
                    "content":    doc,
                    "metadata":   meta
                })
        except Exception:
            pass

    return results[:n]

def get_context(query: str, n: int = 3) -> str:
    """Get memory context string for AI prompts."""
    memories = search(query, n)
    if not memories:
        return ""
    ctx = "## Relevant Past Context:\n\n"
    for m in memories:
        ts  = m["metadata"].get("ts", "")[:10]
        ctx += (f"**[{m['collection']} — {ts}]**\n"
                f"{m['content'][:250]}\n\n")
    return ctx

def get_findings(target: str = None,
                 severity: str = None) -> list:
    """Get security findings, optionally filtered."""
    _ensure_init()
    if not _available or not _findings:
        return []
    try:
        where = {}
        if target:
            where["target"] = target
        if severity:
            where["severity"] = severity
        res = (_findings.get(where=where)
               if where else _findings.get())
        return list(zip(
            res.get("documents", []),
            res.get("metadatas", [])
        ))
    except Exception:
        return []

# ── Stats & Management ────────────────────────────────────────

def stats() -> dict:
    """Get memory statistics."""
    _ensure_init()
    if not _available:
        return {"error": "Memory not available"}
    try:
        return {
            "conversations": _conversations.count(),
            "research":      _research.count(),
            "findings":      _findings.count(),
            "tasks":         _tasks.count(),
            "total":         sum([
                _conversations.count(),
                _research.count(),
                _findings.count(),
                _tasks.count()
            ])
        }
    except Exception:
        return {"error": "Could not get stats"}

def clear(collection: str = "all") -> str:
    """Clear memory collections."""
    global _conversations, _research, _findings, _tasks
    _ensure_init()
    if not _available or not _client:
        return "Memory not available"
    try:
        cols = (["conversations","research","findings","tasks"]
                if collection == "all" else [collection])
        for c in cols:
            _client.delete_collection(c)
        _conversations = _client.get_or_create_collection("conversations")
        _research      = _client.get_or_create_collection("research")
        _findings      = _client.get_or_create_collection("findings")
        _tasks         = _client.get_or_create_collection("tasks")
        return f"✅ Cleared: {', '.join(cols)}"
    except Exception as e:
        return f"Error: {e}"

# Auto-initialize on import
init()

if __name__ == "__main__":
    print("🧠 Memory Module Test")
    print(f"Stats: {stats()}")
    save_research("Test", "This is a test memory entry",
                  tags=["test"])
    results = search("test memory")
    print(f"Search results: {len(results)}")
    for r in results:
        print(f"  [{r['collection']}] {r['content'][:80]}")
