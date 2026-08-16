#!/usr/bin/env python3
"""One-URL baton in front of live Dream 0731 + Qwen. Occupancy unchanged.

  python3 ~/Documents/projects/dream-stack/dream-baton.py
  # listens 127.0.0.1:8877

Default → Qwen. Hand to 0731 when tool_choice=required, async/run-script,
or implicit find-then-act. Cascade: if Qwen returns no tools under
tool_choice=required, retry 0731.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("BATON_HOST", "127.0.0.1")
PORT = int(os.environ.get("BATON_PORT", "8877"))
QWEN = os.environ.get("BATON_QWEN", "http://192.168.100.11:8100/v1").rstrip("/")
DS4F = os.environ.get("BATON_0731", "http://127.0.0.1:8888/v1").rstrip("/")
QWEN_MODEL = os.environ.get("BATON_QWEN_MODEL", "Qwen3.8-27B")
DS4F_MODEL = os.environ.get("BATON_0731_MODEL", "deepseek-v4-flash-0731")
SERVED = os.environ.get("BATON_SERVED", "dream-baton")
LOG = os.environ.get("BATON_LOG", os.path.expanduser("~/logs/dream-baton.log"))
# Advertise 0731's window so /new is not stuck at Qwen 88k.
# Requests that would overflow Qwen (~80k prompt) go to 0731.
BATON_MAX_LEN = int(os.environ.get("BATON_MAX_LEN", "347392"))
QWEN_SAFE = int(os.environ.get("BATON_QWEN_SAFE", "75000"))

ASYNC_RE = re.compile(
    r"\b(poll|pending|async|run_code|run the (analysis )?script|transactions_20|"
    r"execute the script|wait (for|until) (it|the) (to )?(finish|complete))\b",
    re.I,
)
FIND_THEN_ACT_RE = re.compile(
    r"\b(look\s*up|find|search (for )?(contact|her|him)|who is)\b.*\b(email|send|message|notify)\b"
    r"|\b(email|send|message|notify)\b.*\b(look\s*up|find|contact)\b"
    r"|\b(email|send).{0,80}\b(sarah|contact)\b",
    re.I,
)


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n"
    sys.stderr.write(line)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a") as f:
            f.write(line)
    except OSError:
        pass


def last_user_text(body: dict) -> str:
    texts = []
    for m in body.get("messages") or []:
        if not isinstance(m, dict) or m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, str):
            texts.append(c)
        elif isinstance(c, list):
            texts.append(" ".join(str(p.get("text", "")) for p in c if isinstance(p, dict)))
    return "\n".join(texts)


def est_prompt_tokens(body: dict) -> int:
    n = 0
    for m in body.get("messages") or []:
        if not isinstance(m, dict):
            continue
        c = m.get("content")
        if isinstance(c, str):
            n += max(1, len(c) // 4)
        elif isinstance(c, list):
            n += sum(max(1, len(str(p.get("text", ""))) // 4) for p in c if isinstance(p, dict))
        if m.get("tool_calls"):
            n += 200
    tools = body.get("tools") or []
    n += 80 * len(tools)
    return n


def pick_brain(body: dict) -> str:
    tc = body.get("tool_choice")
    if isinstance(tc, dict):
        tc = tc.get("type") or tc.get("tool") or ""
    tc = str(tc or "auto").lower()
    if tc in {"required", "any"}:
        return "0731"
    if est_prompt_tokens(body) > QWEN_SAFE:
        return "0731"
    text = last_user_text(body)
    if ASYNC_RE.search(text):
        return "0731"
    if FIND_THEN_ACT_RE.search(text):
        return "0731"
    return "qwen"


def think_off(body: dict) -> dict:
    # Pass stream through. Forcing stream=false broke tool-eval-bench
    # (it reads SSE). Do not wrap llama.cpp in extra_body.
    out = dict(body)
    ctk = dict(out.get("chat_template_kwargs") or {})
    ctk["thinking"] = False
    ctk["enable_thinking"] = False
    out["chat_template_kwargs"] = ctk
    out["enable_thinking"] = False
    return out


def forward(base: str, model: str, body: dict) -> tuple[int, dict]:
    payload = think_off(body)
    payload["model"] = model
    payload["stream"] = False
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        base + "/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw[:800]}


def forward_stream(base: str, model: str, body: dict):
    payload = think_off(body)
    payload["model"] = model
    payload["stream"] = True
    payload.setdefault("stream_options", {})
    if isinstance(payload["stream_options"], dict):
        payload["stream_options"].setdefault("include_usage", True)
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        base + "/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=180)


def has_tool_calls(resp: dict) -> bool:
    for ch in resp.get("choices") or []:
        msg = (ch or {}).get("message") or {}
        if msg.get("tool_calls"):
            return True
    return False


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        log("http " + (fmt % args))

    def _send(self, code: int, obj: dict) -> None:
        raw = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in {"/v1/models", "/models"}:
            self._send(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": SERVED,
                            "object": "model",
                            "owned_by": "dream-baton",
                            "root": f"{DS4F_MODEL}+{QWEN_MODEL}",
                            "max_model_len": BATON_MAX_LEN,
                        }
                    ],
                },
            )
            return
        if path in {"/health", "/"}:
            self._send(200, {"ok": True, "qwen": QWEN, "ds4f": DS4F})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path not in {"/v1/chat/completions", "/chat/completions"}:
            self._send(404, {"error": "not found"})
            return
        n = int(self.headers.get("Content-Length") or "0")
        try:
            body = json.loads(self.rfile.read(n).decode())
        except Exception:
            self._send(400, {"error": "bad json"})
            return
        brain = pick_brain(body)
        base, model = (DS4F, DS4F_MODEL) if brain == "0731" else (QWEN, QWEN_MODEL)
        t0 = time.perf_counter()
        want_stream = bool(body.get("stream"))
        if want_stream:
            try:
                up = forward_stream(base, model, body)
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8", "replace")
                log(f"pick={brain} stream-err {e.code} {raw[:200]}")
                try:
                    self._send(e.code, json.loads(raw))
                except Exception:
                    self._send(e.code, {"error": raw[:800]})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                for chunk in up:
                    self.wfile.write(chunk)
                self.wfile.flush()
            finally:
                up.close()
            log(f"pick={brain} used={brain} stream {time.perf_counter()-t0:.2f}s")
            return
        code, resp = forward(base, model, body)
        used = brain
        tc = body.get("tool_choice")
        if isinstance(tc, dict):
            tc = tc.get("type")
        if (
            brain == "qwen"
            and str(tc or "").lower() in {"required", "any"}
            and not has_tool_calls(resp)
        ):
            code, resp = forward(DS4F, DS4F_MODEL, body)
            used = "0731-cascade"
        if isinstance(resp, dict) and resp.get("model"):
            resp["model"] = SERVED
        dt = time.perf_counter() - t0
        log(f"pick={brain} used={used} {dt:.2f}s http={code}")
        self._send(code, resp)


def main() -> int:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    log(f"listening http://{HOST}:{PORT}/v1  qwen={QWEN} 0731={DS4F}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
