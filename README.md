# ⚡ ai-router — Universal AI API Router

**Gabungan inovasi: Free AI Access + Smart Routing.**

Satu file Python, zero dependency, bisa pake AI gratis dari berbagai provider tanpa ribet. Auto-fallback kalau kena rate limit.

---

## 🚀 Cara Pake

### 1. Setup API Key

Bikin file `.env` di folder yang sama:

```env
# Daftar gratis di masing-masing provider, bebas pilih salah satu/beberapa
GROQ_API_KEY=gsk_xxx          → groq.com (free, fast)
GEMINI_API_KEY=AIzaxxx         → aistudio.google.com (free tier paling generous)
DEEPSEEK_API_KEY=sk-xxx       → platform.deepseek.com
TOGETHER_API_KEY=xxx           → together.ai ($25 credit gratis)
HF_API_KEY=hf_xxx              → huggingface.co (free inference)
```

**Minimal 1 aja udah cukup.** Makin banyak makin bagus buat fallback.

### 2. CLI Mode

```bash
python ai_router.py "cara bikin nasi goreng enak"
python ai_router.py --prefer groq "apa itu AI?"
python ai_router.py --providers   # cek status semua provider
```

### 3. Server Mode

```bash
python ai_router.py --serve
# → http://localhost:8080
```

Ada UI web sederhana. Bisa juga pake curl:

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "apa itu AI router?"}'
```

---

## 🔧 Cara Kerja

```
Prompt kamu
    ↓
  ai-router → cek provider 1 (Gemini)  → ✅ berhasil → balik hasil
              ↓ (gagal / rate limit)
              cek provider 2 (Groq)     → ✅ berhasil → balik hasil
              ↓ (gagal)
              cek provider 3 (DeepSeek) → dst...
```

- **Prioritas otomatis:** coba provider yang API key-nya ada
- **Auto-fallback:** kalau kena rate limit / quota habis, pindah provider berikutnya
- **Zero dependency:** cuma pake std library Python, gak perlu `pip install`

---

## 📦 File Size

| File | Size |
|------|------|
| `ai_router.py` | ~12 KB |
| `README.md` | ~1.5 KB |
| **Total** | **< 15 KB** |

---

## 🎯 Kenapa Ini Keren

- ✅ **Gratis** — pake free tier dari berbagai provider AI
- ✅ **Ringan** — 1 file, bisa di-copy paste ke server mana aja
- ✅ **Zero dep** — standar library Python aja cukup
- ✅ **Auto fallback** — kalau satu lemot/error, pindah sendiri
- ✅ **CLI + Web UI + API** — 3 mode dalam 1 file
- ✅ **Privacy** — data ke provider langsung, gak lewat server pihak ketiga

---

## 📜 License

MIT — bebas pake, bebas modif, bebas sebar.
