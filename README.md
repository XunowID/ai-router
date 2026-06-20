# ⚡ ai-router — Universal AI API Router

**Combine free AI access with smart routing.**  
Single Python file, zero dependencies, auto-fallback across multiple providers.

---

## 🚀 Quick Start

### 1. Get API Keys

Create a `.env` file:

```env
GROQ_API_KEY=gsk_xxx          → groq.com (free, blazing fast)
GEMINI_API_KEY=AIzaxxx         → aistudio.google.com (most generous free tier)
DEEPSEEK_API_KEY=sk-xxx       → platform.deepseek.com
TOGETHER_API_KEY=xxx           → together.ai ($25 free credit)
HF_API_KEY=hf_xxx              → huggingface.co (free inference)
```

**One key is enough.** More keys = better fallback coverage.

### 2. CLI Mode

```bash
python ai_router.py "explain quantum computing in simple terms"
python ai_router.py --prefer groq "what is AI?"
python ai_router.py --providers   # check which APIs are configured
```

### 3. Server Mode

```bash
python ai_router.py --serve
# → http://localhost:8080
```

Comes with a web UI. Also works with curl:

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "what is an AI router?"}'
```

---

## 🔧 How It Works

```
Your prompt
    ↓
  ai-router → try Gemini      → ✅ success → return result
              ↓ (rate limited)
              try Groq         → ✅ success → return result
              ↓ (failed)
              try DeepSeek     → continue...
```

- **Auto-priority:** tries configured providers in smart order
- **Auto-fallback:** on rate limit / quota exceeded, moves to next provider
- **Zero dependencies:** pure Python standard library — no `pip install`
- **Privacy-first:** your data goes directly to the provider, no middleman

---

## 📦 Size

| File | Size |
|------|------|
| `ai_router.py` | ~12 KB |
| `README.md` | ~1.5 KB |
| **Total** | **< 15 KB** |

---

## 🎯 Why This Exists

- ✅ **Free** — leverages free tiers of multiple AI providers
- ✅ **Lightweight** — one file, copy-paste anywhere
- ✅ **Zero deps** — Python stdlib only, works out of the box
- ✅ **Auto fallback** — one provider down? Next one takes over
- ✅ **3 modes** — CLI + Web UI + REST API in a single file
- ✅ **Extensible** — add any OpenAI-compatible provider in 3 lines

---

## 🤝 Contributing

PRs welcome! Add providers, improve routing, fix bugs — all contributions help.

---

## 📜 License

MIT — use it, modify it, share it. No strings attached.
