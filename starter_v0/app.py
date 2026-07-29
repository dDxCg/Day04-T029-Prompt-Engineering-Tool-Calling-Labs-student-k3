from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_file

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
DEFAULT_UI = ROOT.parent / "prototype.html"

KEYED_CONNECTIONS = [
    ("Tavily", "TAVILY_API_KEY", "Tool <code>lookup</code> — tìm tin trên web."),
    ("Firecrawl", "FIRECRAWL_API_KEY", "Tool <code>fetch</code> — mở URL ra đọc."),
    ("RapidAPI Twitter", "RAPIDAPI_KEY", "Tool <code>timeline</code>, <code>social_search</code>."),
    ("Telegram", "TELEGRAM_BOT_TOKEN", "Tool <code>send</code> — hành động nhạy cảm, luôn hỏi trước."),
]
KEYLESS_CONNECTIONS = [
    ("arXiv", "Tool <code>papers</code>, <code>paper_text</code>."),
    ("Wikipedia", "Tool <code>wiki_lookup</code>."),
    ("Company policy", "Tool <code>policy</code> — đọc file Markdown cục bộ."),
]

app = Flask(__name__)
config: dict[str, Any] = {}
transcript: dict[str, Any] = {}
transcript_path: Path


def tool_event_view(event: dict[str, Any]) -> dict[str, Any]:
    result = event.get("result")
    summary = ""
    error = None
    if isinstance(result, dict):
        error = result.get("error")
        if error:
            summary = str(result.get("message") or error)
        elif isinstance(result.get("items"), list):
            summary = f"{len(result['items'])} kết quả"
        elif result.get("markdown"):
            summary = f"digest {len(result['markdown'])} ký tự"
        elif result.get("status"):
            summary = str(result["status"])
    return {
        "tool": event.get("tool"),
        "args": event.get("args") or {},
        "ok": bool(event.get("ok", True)),
        "ms": int(event.get("ms") or 0),
        "round": int(event.get("round") or 1),
        "summary": summary,
        "error": error,
    }


@app.get("/")
def index():
    return send_file(config["ui_path"])


@app.get("/api/meta")
def api_meta():
    connections = [
        {"name": name, "note": note, "state": "ok" if os.getenv(env) else "missing"}
        for name, env, note in KEYED_CONNECTIONS
    ]
    connections += [{"name": name, "note": note, "state": "keyless"} for name, note in KEYLESS_CONNECTIONS]
    return jsonify({
        "transcript_id": transcript["transcript_id"],
        "artifact_version": transcript["artifact_version"],
        "provider": config["provider_name"],
        "model": config["model"],
        "max_tool_rounds": config["max_tool_rounds"],
        "history_window": config["history_window"],
        "turn_count": len(transcript["turns"]),
        "connections": connections,
    })


@app.post("/api/chat")
def api_chat():
    payload = request.get_json(silent=True) or {}
    user_text = str(payload.get("message") or "").strip()
    if not user_text:
        return jsonify({"error": "empty_message"}), 400

    history = [
        {"role": item["role"], "content": str(item["content"])}
        for item in payload.get("history") or []
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"} and item.get("content")
    ]
    max_tool_rounds = int(payload.get("max_tool_rounds") or config["max_tool_rounds"])
    history_window = int(payload.get("history_window") or config["history_window"])

    messages = [
        {"role": "system", "content": config["system_prompt"]},
        *trim_history(history, history_window),
        {"role": "user", "content": user_text},
    ]

    turn_index = len(transcript["turns"]) + 1
    turn_record: dict[str, Any] = {
        "turn_index": turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    started = time.perf_counter()
    try:
        result = run_model_tool_loop(
            provider=config["provider"],
            messages=messages,
            tools=config["openai_tools"],
            model=config["model"],
            max_tool_rounds=max_tool_rounds,
        )
        turn_record.update(result)
    except Exception as exc:
        turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {str(exc)}"})

    total_ms = round((time.perf_counter() - started) * 1000)
    turn_record["ended_at"] = now_iso()
    turn_record["total_ms"] = total_ms
    transcript["turns"].append(turn_record)
    write_transcript(transcript_path, transcript)

    events = [tool_event_view(event) for event in turn_record.get("tool_events", [])]
    tool_ms = sum(event["ms"] for event in events)
    model_ms = sum(int(round_record.get("model_ms") or 0) for round_record in turn_record.get("rounds", []))
    slowest = max(events, key=lambda event: event["ms"], default=None)

    return jsonify({
        "status": turn_record["status"],
        "assistant_text": turn_record.get("assistant_text") or "",
        "error": turn_record.get("error"),
        "turn_index": turn_index,
        "rounds_used": len(turn_record.get("rounds", [])),
        "max_tool_rounds": max_tool_rounds,
        "tool_events": events,
        "latency": {
            "total_ms": total_ms,
            "model_ms": model_ms,
            "tool_ms": tool_ms,
            "slowest_tool": slowest["tool"] if slowest else None,
            "slowest_ms": slowest["ms"] if slowest else 0,
        },
        "transcript_id": transcript["transcript_id"],
        "transcript_path": str(transcript_path),
    })


@app.get("/api/transcript")
def api_transcript():
    return jsonify(transcript)


def main() -> None:
    # Tool-loop logging prints emoji; Windows consoles default to cp1252 and would raise.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Research Agent web UI backed by the real agent tool loop.")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic", "gemini"], required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", required=True, help="Artifact version label, e.g. v3.")
    parser.add_argument("--system-prompt", type=Path, default=ARTIFACTS_DIR / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    parser.add_argument("--ui", type=Path, default=DEFAULT_UI)
    parser.add_argument("--transcripts-dir", type=Path, default=ROOT / "transcripts")
    parser.add_argument("--history-window", type=int, default=5)
    parser.add_argument("--max-tool-rounds", type=int, default=4)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    provider = make_provider(args.provider)
    artifact_version = build_artifact_version(args.version, args.system_prompt, args.tools)
    tool_declarations = load_tool_declarations(args.tools)

    config.update({
        "provider": provider,
        "provider_name": args.provider,
        "model": args.model or getattr(provider, "default_model", None),
        "system_prompt": args.system_prompt.read_text(encoding="utf-8"),
        "openai_tools": to_openai_tools(tool_declarations),
        "max_tool_rounds": args.max_tool_rounds,
        "history_window": args.history_window,
        "ui_path": args.ui.resolve(),
    })

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(args.version), safe_slug(args.provider), "ui", timestamp])
    global transcript_path
    transcript_path = args.transcripts_dir / f"{transcript_id}.transcript.json"
    transcript.update({
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": args.provider,
        "model": config["model"],
        "system_prompt": str(args.system_prompt),
        "tools": str(args.tools),
        "history_window": args.history_window,
        "max_tool_rounds": args.max_tool_rounds,
        "surface": "web_ui",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    })

    print(f"Research Agent UI: http://{args.host}:{args.port}")
    print(f"artifact_version={artifact_version.artifact_version}")
    print(f"transcript: {transcript_path}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
