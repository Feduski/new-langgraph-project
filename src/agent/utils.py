from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


HANDLE_RE = re.compile(r"(^|\s)(@[A-Za-z0-9_]{1,15})(\s|$)")


def extract_handle(text_or_parts: Any) -> Optional[str]:
    text = message_text(text_or_parts)
    if not text:
        return None
    m = HANDLE_RE.search(text.strip())
    return m.group(2) if m else None


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_prompt(prompts_dir: Path, filename: str) -> str:
    return (prompts_dir / filename).read_text(encoding="utf-8")


def dumps(obj: Any) -> str:
    # JSON estable para LLM (sin ASCII escape)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def build_evidence_pack(handle: str, results_a: List[dict], results_b: List[dict]) -> Dict[str, Any]:
    """
    Best-effort evidence pack from Tavily. Metrics/dates usually unknown.
    """
    merged = (results_a or []) + (results_b or [])
    merged = merged[:20]

    posts = []
    visuals = 0

    for r in merged:
        url = r.get("url") or ""
        title = (r.get("title") or "").strip()
        content = (r.get("content") or "").strip()

        ptype = "post" if "/status/" in url else "post"
        text = content[:280] if content else (title[:280] if title else "paraphrase: content not visible")

        note_bits = []
        if "image" in content.lower() or "screenshot" in content.lower():
            visuals += 1
            note_bits.append("mentions visual/screenshot (in snippet)")

        posts.append({
            "type": ptype,
            "date": "unknown",
            "text": text if content else f"paraphrase: {text}",
            "link": url,
            "visible_metrics": {"likes": "unknown", "reposts": "unknown", "replies": "unknown"},
            "notes": ", ".join(note_bits) if note_bits else ""
        })

    sample_counts = {
        "posts": len(posts),
        "qts": 0,
        "rts": 0,
        "replies": 0,
        "visuals": visuals,
        "threads": 0,
    }

    return {
        "handle": handle,
        "timestamp_utc": now_iso_utc(),
        "confidence": "Medium" if posts else "Low",
        "limitations": [
            "Tavily results may not expose replies/QTs/RTs/metrics reliably.",
            "Dates/metrics marked unknown when not visible.",
        ],
        "profile": {
            "display_name": "",
            "bio": "",
            "verified": "unknown",
            "link_in_bio": "",
            "niche_guess": "",
        },
        "last_30d_samples": {
            "posts": posts[:18],
            "replies": [],
            "discussions": [],
        },
        "derived_signals": {
            "sample_counts": sample_counts,
            "format_mix_notes": [],
            "repeated_targets": [],
            "observed_themes": [],
            "receipts_observed": [],
        }
    }

def message_text(content: Any) -> str:
    # content puede ser str o lista de parts (dicts) tipo [{"type":"text","text":"..."}]
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict):
                # formatos comunes: {"type":"text","text": "..."}
                if "text" in part and isinstance(part["text"], str):
                    chunks.append(part["text"])
        return "\n".join(chunks)
    return ""