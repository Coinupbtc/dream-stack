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
import threading
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
# Advertise 0731's window so /new is not stuck at Qwen leftover.
# Live roommate n_ctx=116224. Hand off before that wall; 400 still retries 0731.
# Option 1 (SAFE ~80k) parked — do not drop until asked.
BATON_MAX_LEN = int(os.environ.get("BATON_MAX_LEN", "347392"))
QWEN_CTX = int(os.environ.get("BATON_QWEN_CTX", "116224"))
QWEN_SAFE = int(os.environ.get("BATON_QWEN_SAFE", "100000"))
# n2 traffic cop: fat Qwen prefill and 0731 decode share box-2 UMA.
# Don't start one while the other is in flight. Short Qwen chats skip the lock.
N2_FAT = int(os.environ.get("BATON_N2_FAT", "24000"))
N2_WAIT = float(os.environ.get("BATON_N2_WAIT", "30"))
_n2_cv = threading.Condition()
_n2_0731 = 0
_n2_qwen_fat = 0

# Run/poll a named script or job — not "run the numbers" chat.
ASYNC_RE = re.compile(
    r"\b(?:run|execute|launch)\b.{0,80}\b(?:script|analysis|job)\b"
    r"|\b(?:poll|pending|async|run_code)\b"
    r"|\bwait\s+(?:for|until)\b.{0,40}\b(?:finish|complete|done|ready)\b"
    r"|\b\w+\(\s*source\s*=",
    re.I,
)
# Lookup-then-act, or implicit notify a named person (not "let me know" / "tell me").
# Multi-step research/report chains: 0731 same score, ~2× faster on the long ones.
RESEARCH_RE = re.compile(
    r"\b(?:put together|compile|draft|write)\b.{0,60}\b(?:report|analysis|brief)\b"
    r"|\b(?:competitor|competitive|quarterly)\s+(?:analysis|performance|report)\b"
    r"|\b(?:research|analysis)\s+report\b",
    re.I,
)
FIND_THEN_ACT_RE = re.compile(
    r"\b(look\s*up|find|search (for )?(contact|her|him)|who is)\b.*\b(email|send|message|notify)\b"
    r"|\b(email|send|message|notify)\b.*\b(look\s*up|find|contact)\b"
    r"|\blet\s+(?!me\b|us\b)[\w.'-]+(?:\s+[\w.'-]+)?\s+know\b"
    r"|\b(?:tell|inform|notify)\s+(?!me\b|us\b)[\w.'-]+(?:\s+[\w.'-]+)?\b"
    r".{0,80}\b(?:that|about|meeting|moved|email|message)\b",
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


def _chars(obj) -> int:
    if obj is None:
        return 0
    if isinstance(obj, str):
        return len(obj)
    if isinstance(obj, list):
        return sum(_chars(p.get("text") if isinstance(p, dict) else p) for p in obj)
    if isinstance(obj, dict):
        try:
            return len(json.dumps(obj, default=str))
        except TypeError:
            return len(str(obj))
    return len(str(obj))


def est_prompt_tokens(body: dict) -> int:
    # Dense JSON / tool dumps are ~3 chars/token. //4 missed the 88k wall.
    n = 0
    for m in body.get("messages") or []:
        if not isinstance(m, dict):
            continue
        n += max(1, _chars(m.get("content")) // 3)
        tc = m.get("tool_calls")
        if tc:
            n += max(80, _chars(tc) // 3)
        if m.get("role") == "tool":
            n += 40
    tools = body.get("tools") or []
    n += 100 * len(tools)
    return n


def is_ctx_overflow(err_obj, raw: str = "") -> bool:
    blob = raw or ""
    if isinstance(err_obj, dict):
        try:
            blob += json.dumps(err_obj)
        except TypeError:
            blob += str(err_obj)
    s = blob.lower()
    return (
        "exceed_context" in s
        or "exceeds the available context" in s
        or "context length" in s
        or "maximum context" in s
    )


class N2Slot:
    """Serialize fat Qwen prefills vs any 0731 call (both hit node2 leftover)."""

    def __init__(self, kind: str | None):
        self.kind = kind

    def __enter__(self):
        global _n2_0731, _n2_qwen_fat
        if not self.kind:
            return self
        deadline = time.monotonic() + N2_WAIT
        with _n2_cv:
            while True:
                conflict = (
                    (self.kind == "qwen_fat" and _n2_0731 > 0)
                    or (self.kind == "0731" and _n2_qwen_fat > 0)
                )
                if not conflict:
                    break
                left = deadline - time.monotonic()
                if left <= 0:
                    log(
                        f"n2-cop timeout kind={self.kind} "
                        f"0731={_n2_0731} qfat={_n2_qwen_fat}"
                    )
                    break
                _n2_cv.wait(timeout=left)
            if self.kind == "0731":
                _n2_0731 += 1
            else:
                _n2_qwen_fat += 1
            log(f"n2-cop enter kind={self.kind} 0731={_n2_0731} qfat={_n2_qwen_fat}")
        return self

    def __exit__(self, *exc):
        global _n2_0731, _n2_qwen_fat
        if not self.kind:
            return False
        with _n2_cv:
            if self.kind == "0731":
                _n2_0731 = max(0, _n2_0731 - 1)
            else:
                _n2_qwen_fat = max(0, _n2_qwen_fat - 1)
            _n2_cv.notify_all()
        return False


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
    if RESEARCH_RE.search(text):
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
            self._send(
                200,
                {
                    "ok": True,
                    "qwen": QWEN,
                    "ds4f": DS4F,
                    "n2_0731": _n2_0731,
                    "n2_qwen_fat": _n2_qwen_fat,
                    "n2_fat": N2_FAT,
                },
            )
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
        est = est_prompt_tokens(body)
        slot = "0731" if brain == "0731" else ("qwen_fat" if est >= N2_FAT else None)
        with N2Slot(slot):
            self._forward_locked(body, brain, base, model, est, want_stream, t0)

    def _forward_locked(self, body, brain, base, model, est, want_stream, t0) -> None:
        if want_stream:
            used = brain
            try:
                up = forward_stream(base, model, body)
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8", "replace")
                parsed = None
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = None
                if brain == "qwen" and is_ctx_overflow(parsed, raw):
                    log(f"pick=qwen est={est} stream-overflow → 0731 {raw[:160]}")
                    try:
                        up = forward_stream(DS4F, DS4F_MODEL, body)
                        used = "0731-overflow"
                    except urllib.error.HTTPError as e2:
                        raw2 = e2.read().decode("utf-8", "replace")
                        log(f"pick=qwen 0731-overflow-err {e2.code} {raw2[:200]}")
                        try:
                            self._send(e2.code, json.loads(raw2))
                        except Exception:
                            self._send(e2.code, {"error": raw2[:800]})
                        return
                else:
                    log(f"pick={brain} est={est} stream-err {e.code} {raw[:200]}")
                    try:
                        self._send(e.code, parsed if isinstance(parsed, dict) else {"error": raw[:800]})
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
            log(f"pick={brain} used={used} est={est} stream {time.perf_counter()-t0:.2f}s")
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
        elif brain == "qwen" and code >= 400 and is_ctx_overflow(resp):
            log(f"pick=qwen est={est} overflow → 0731")
            code, resp = forward(DS4F, DS4F_MODEL, body)
            used = "0731-overflow"
        if isinstance(resp, dict) and resp.get("model"):
            resp["model"] = SERVED
        dt = time.perf_counter() - t0
        log(f"pick={brain} used={used} est={est} {dt:.2f}s http={code}")
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
