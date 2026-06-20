#!/usr/bin/env python3
"""
ai-router — Universal AI API Router
Multi-provider with auto-fallback, CLI + API server, zero dependency (stdlib only).
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ─── Minimal HTTP ───────────────────────────────────────────────────
# stdlib only — no pip install needed

try:
    import urllib.request as req_lib
    import urllib.error as url_err

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def _req_json(url: str, data: dict | None = None, headers: dict | None = None) -> dict:
    """HTTP request → JSON. Pure stdlib, zero dependencies."""
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    body = json.dumps(data).encode() if data else None
    r = req_lib.Request(url, data=body, headers=hdrs, method="POST" if data else "GET")
    try:
        with req_lib.urlopen(r, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except url_err.HTTPError as e:
        err_body = e.read().decode() if e.fp else "{}"
        return {"error": f"HTTP {e.code}: {err_body}"}
    except Exception as e:
        return {"error": str(e)}


# ─── Provider Config ────────────────────────────────────────────────


@dataclass
class Provider:
    name: str
    url: str
    model: str
    api_key_env: str
    headers_fn: callable = lambda self, key: {"Authorization": f"Bearer {key}"}
    body_fn: callable = lambda self, prompt, model: {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    resp_fn: callable = lambda self, data: (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", json.dumps(data, indent=2))
    )
    fallback_on: list = field(default_factory=lambda: ["rate", "limit", "429", "quota"])


PROVIDERS: list[Provider] = [
    Provider(
        name="Groq",
        url="https://api.groq.com/openai/v1/chat/completions",
        model="llama-3.3-70b-versatile",
        api_key_env="GROQ_API_KEY",
    ),
    Provider(
        name="Gemini",
        url="https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        model="gemini-2.0-flash",
        api_key_env="GEMINI_API_KEY",
        headers_fn=lambda self, key: {"x-goog-api-key": key, "Content-Type": "application/json"},
        body_fn=lambda self, prompt, model: {
            "contents": [{"parts": [{"text": prompt}]}]
        },
        resp_fn=lambda self, data: (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", json.dumps(data, indent=2))
        ),
    ),
    Provider(
        name="DeepSeek",
        url="https://api.deepseek.com/v1/chat/completions",
        model="deepseek-chat",
        api_key_env="DEEPSEEK_API_KEY",
    ),
    Provider(
        name="Together AI",
        url="https://api.together.xyz/v1/chat/completions",
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        api_key_env="TOGETHER_API_KEY",
    ),
    Provider(
        name="HuggingFace",
        url="https://api-inference.huggingface.co/models/{model}/v1/chat/completions",
        model="microsoft/Phi-3.5-mini-instruct",
        api_key_env="HF_API_KEY",
        headers_fn=lambda self, key: {"Authorization": f"Bearer {key}"},
        body_fn=lambda self, prompt, model: {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        },
    ),
]


# ─── Core Router ────────────────────────────────────────────────────


def get_api_key(env_var: str) -> str | None:
    return os.getenv(env_var) or os.getenv(env_var.lower())


def ask_provider(provider: Provider, prompt: str) -> dict:
    """Send prompt to a single provider, return raw response dict."""
    key = get_api_key(provider.api_key_env)
    if not key:
        return {"error": f"{provider.api_key_env} not set"}

    url = provider.url.format(model=provider.model)
    headers = provider.headers_fn(provider, key)
    body = provider.body_fn(provider, prompt, provider.model)

    return _req_json(url, data=body, headers=headers)


def is_error(data: dict) -> str | None:
    """Check if response contains an error. Return reason string or None."""
    err = data.get("error")
    if not err:
        return None
    err_str = str(err).lower()
    for kw in PROVIDERS[0].fallback_on:
        if kw in err_str:
            return str(err)
    return None


def ai_route(prompt: str, prefer: str | None = None) -> str:
    """Route prompt to the best available provider with auto-fallback."""
    if not HAS_REQUESTS:
        return "[ERROR] Python stdlib urllib unavailable."

    if not prompt.strip():
        return "[ERROR] Empty prompt."

    # Order: preferred first (if set), then Gemini (most generous free tier), then others
    if prefer:
        ordered = [p for p in PROVIDERS if p.name.lower() == prefer.lower()]
        ordered += [p for p in PROVIDERS if p.name.lower() != prefer.lower()]
    else:
        ordered = sorted(PROVIDERS, key=lambda p: (p.name != "Gemini", p.name != "Groq"))

    for provider in ordered:
        key = get_api_key(provider.api_key_env)
        if not key:
            continue

        sys.stderr.write(f"  → {provider.name} ({provider.model}) ... ")
        data = ask_provider(provider, prompt)
        reason = is_error(data)

        if reason:
            sys.stderr.write(f"⏭ skip ({reason[:60]})\n")
            continue

        result = provider.resp_fn(provider, data)
        if result and not result.startswith("{"):
            sys.stderr.write(f"✅ OK\n\n")
            return result.strip()

        sys.stderr.write(f"⏭ skip (empty/unexpected)\n")

    return (
        "[ERROR] All providers failed.\n"
        "Set at least one API key in .env file.\n"
        "See README.md for setup instructions."
    )


# ─── CLI ────────────────────────────────────────────────────────────


def cli_main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ai-router — Universal AI API Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python ai_router.py \"explain quantum computing in simple terms\"\n"
            "  python ai_router.py --prefer groq \"what is AI?\"\n"
            "  python ai_router.py --serve\n"
            "  python ai_router.py --providers\n"
            "\nEnvironment variables:\n"
            "  GROQ_API_KEY | GEMINI_API_KEY | DEEPSEEK_API_KEY\n"
            "  TOGETHER_API_KEY | HF_API_KEY\n"
        ),
    )
    parser.add_argument("prompt", nargs="?", help="Your prompt for the AI")
    parser.add_argument("--prefer", "-p", help="Preferred provider (groq, gemini, etc)")
    parser.add_argument("--serve", "-s", action="store_true", help="Run as HTTP API server")
    parser.add_argument("--providers", action="store_true", help="List all available providers and their status")
    parser.add_argument("--port", type=int, default=8080, help="Port for server mode (default: 8080)")
    args = parser.parse_args()

    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))

    if args.providers:
        print("📡 Available Providers:\n")
        for p in PROVIDERS:
            key = get_api_key(p.api_key_env)
            status = "✅" if key else "❌ no key"
            print(f"  {p.name:15s} {p.model:45s} {status}")
        return

    if args.serve:
        return serve_mode(args.port)

    if not args.prompt:
        parser.print_help()
        return

    result = ai_route(args.prompt, prefer=args.prefer)
    print(result)


# ─── Server Mode ────────────────────────────────────────────────────


def serve_mode(port: int):
    """Simple HTTP server — zero deps, pure Python stdlib."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class RouterHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            try:
                data = json.loads(body)
                prompt = data.get("prompt", "")
                prefer = data.get("prefer")
                result = ai_route(prompt, prefer)
                self._json({"response": result})
            except Exception as e:
                self._json({"error": str(e)}, 400)

        def do_GET(self):
            if self.path == "/":
                self._html()
            elif self.path == "/providers":
                info = [
                    {
                        "name": p.name,
                        "model": p.model,
                        "configured": bool(get_api_key(p.api_key_env)),
                    }
                    for p in PROVIDERS
                ]
                self._json({"providers": info})
            else:
                self._json({"error": "not found"}, 404)

        def _json(self, data: dict, code: int = 200):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def _html(self):
            html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>ai-router</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0d1117;color:#e6edf3;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px;max-width:560px;width:90%}
h1{font-size:24px;background:linear-gradient(90deg,#58a6ff,#bc8cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.g{color:#8b949e;font-size:14px;margin:8px 0 20px}
textarea{width:100%;background:#0d1117;border:1px solid #30363d;border-radius:8px;color:#e6edf3;padding:12px;font-size:14px;min-height:100px;resize:vertical;outline:none}
textarea:focus{border-color:#58a6ff}
button{background:#238636;border:none;border-radius:8px;color:#fff;padding:10px 24px;font-size:14px;cursor:pointer;margin-top:10px;width:100%}
button:hover{background:#2ea043}
#res{margin-top:14px;padding:12px;background:#0d1117;border:1px solid #30363d;border-radius:8px;font-size:13px;white-space:pre-wrap;display:none}
</style></head><body>
<div class="card">
<h1>⚡ ai-router</h1>
<p class="g">Universal AI API Router — multi-provider, auto-fallback</p>
<textarea id="prompt" placeholder="Type your prompt here ..."></textarea>
<button onclick="ask()">Send →</button>
<div id="res"></div>
</div>
<script>
async function ask(){
const p=document.getElementById('prompt').value.trim();if(!p)return;
const res=document.getElementById('res');res.style.display='block';res.textContent='⏳ loading ...';
const r=await fetch('/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:p})});
const d=await r.json();res.textContent=d.response||d.error;}
</script></body></html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())

        def log_message(self, fmt, *args):
            sys.stderr.write(f"[ai-router] {args[0]} {args[1]} {args[2]}\n")

    server = HTTPServer(("0.0.0.0", port), RouterHandler)
    print(f"⚡ ai-router server running on http://localhost:{port}")
    print(f"   POST / — chat with AI")
    print(f"   GET  /providers — check provider status")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Bye!")
        server.server_close()


# ─── Entry ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli_main()
