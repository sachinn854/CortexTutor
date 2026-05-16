# CortexTutor — AI-Powered YouTube Learning Assistant

An intelligent learning assistant that transforms any YouTube video into an interactive study session. Built with a full RAG (Retrieval-Augmented Generation) pipeline, it extracts video transcripts, builds a semantic knowledge base, and answers questions with pinpoint timestamp references.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![LangChain](https://img.shields.io/badge/LangChain-Latest-orange)
![FAISS](https://img.shields.io/badge/FAISS-Vector_DB-purple)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Demo

**Video loaded — embedded player + transcript ingested into FAISS**
![Video loaded](demo/Screenshot%202026-05-16%20232815.png)

**MCQ Quiz generated from lecture content**
![MCQ Quiz](demo/Screenshot%202026-05-16%20232836.png)

**Auto Study Notes generated**
![Study Notes](demo/Screenshot%202026-05-16%20232850.png)

---

## Features

### Core
- **Semantic Q&A** — Ask anything about the video; answers are grounded in transcript context
- **Timestamp Search** — "What happened at 2:51?" maps directly to the relevant segment
- **Auto Notes** — One-click generation of structured study notes from full lecture context
- **MCQ Quiz** — Generate multiple-choice questions with explanations on demand
- **Conversation Memory** — Maintains context across follow-up questions
- **Source Citations** — Every answer includes the relevant timestamp references

### RAG Pipeline
- **Intelligent Chunking** — 800-char chunks with 150-char overlap, preserving semantic boundaries
- **Hybrid Retrieval** — Combines FAISS semantic search with timestamp-based direct lookup
- **Intent Detection** — Automatically routes between Q&A, summary, and timestamp queries
- **Map-Reduce Summarization** — Processes full transcripts in chunks for notes/MCQ generation
- **Embedding Model** — `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| LLM | Groq (LLaMA 3.3 70B) |
| RAG Framework | LangChain |
| Vector DB | FAISS |
| Embeddings | Sentence Transformers |
| Transcript | youtube-transcript-api + yt-dlp |
| Frontend | Vanilla JS + CSS (no framework) |

---

## Quick Start (Local)

**Prerequisites:** Python 3.10+, Groq API key (free at console.groq.com)

```bash
# 1. Clone
git clone https://github.com/sachinn854/CortexTutor.git
cd CortexTutor

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Create .env file
echo GROQ_API_KEY=your_key_here > .env

# 5. Run
uvicorn app.main:app --reload

# Open http://localhost:8000
```

Paste any YouTube URL → wait ~30s for ingestion → ask questions.

---

## Architecture

```
YouTube URL
    │
    ├─ youtube-transcript-api (primary)
    └─ yt-dlp (fallback)
         │
         ▼
  Transcript (timestamped segments)
         │
         ▼
  LangChain Text Splitter
  (800 char chunks, 150 overlap)
         │
         ▼
  Sentence Transformers Embeddings
         │
         ▼
  FAISS Vector Store
         │
    User Query
         │
         ├─ /notes or /mcqs ──► Full transcript map-reduce ──► LLM
         ├─ Timestamp query  ──► Direct segment lookup      ──► LLM
         └─ General Q&A      ──► Top-5 semantic retrieval   ──► LLM
                                                                 │
                                                                 ▼
                                                       Answer + Source Timestamps
```

### Project Structure

```
CortexTutor/
├── backend/
│   ├── app/
│   │   ├── agents/        # Conversational AI + memory
│   │   ├── api/           # FastAPI endpoints (ingest, chat)
│   │   ├── core/          # Config, LLM init, middleware
│   │   ├── rag/           # Pipeline, retriever, vector store, splitter
│   │   ├── services/      # YouTube transcript loader
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── README.md
```

---

## Deployment Challenges & Learnings

A significant part of this project involved investigating why automated YouTube transcript fetching fails on cloud infrastructure — and what can be done about it.

### What was tried

| Approach | Result | Why |
|---|---|---|
| `youtube-transcript-api` on HF Spaces | ❌ SSLError | YouTube blocks all datacenter IPs at network level |
| `yt-dlp` fallback on HF Spaces | ❌ Sign-in required | Same IP-level block; bot detection triggers |
| Cloudflare Worker → YouTube InnerTube API | ❌ `LOGIN_REQUIRED` | All client types (WEB, ANDROID, IOS, TVHTML5) blocked from CF IPs |
| Browser-side fetch via CORS proxies | ❌ 403 / timeout | Proxies themselves on datacenter IPs |
| Browser-side fetch via Piped API | ❌ Instances down / CORS | Community instances unreliable |
| Cloudflare Worker → Invidious API | ❌ 503 | CF IPs blocked by Invidious instances too |
| Browser-side Invidious (direct) | ❌ No CORS headers | Most instances don't set `Access-Control-Allow-Origin` |

### Root cause

YouTube's bot detection operates at multiple layers:
1. **IP reputation** — All datacenter ASNs (AWS, GCP, Cloudflare, HF Spaces) are flagged
2. **po_token challenge** — A JavaScript-computed proof-of-origin token tied to the browser session; can't be replicated server-side without a real browser
3. **TLS fingerprinting** — Serverless/container environments have different TLS profiles than real browsers

**Result:** `youtube-transcript-api`, `yt-dlp`, and all InnerTube API client types return `LOGIN_REQUIRED` / `Sign in to confirm you're not a bot` from any cloud/serverless IP — regardless of cookies, headers, or client type.

### What actually works

- **Local machine** — Residential IP + real Chrome session = no blocks. All transcript methods work natively.
- **Dedicated VPS with static IP** (e.g., Hetzner, Oracle Cloud) — Persistent IP not flagged by YouTube; server-side fetch works reliably.
- **Manual paste fallback** — UI allows pasting transcript directly from YouTube's "Show transcript" feature as a last resort.

---

## Configuration

```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional (defaults shown)
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=./vector_db
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

---

## Troubleshooting

**"No transcript available"** — Video must have captions enabled. Check YouTube → ⋯ More → Show transcript.

**"Rate limit exceeded"** — Groq free tier is 6000 tokens/min. Wait 60s and retry.

**Transcript fetch fails on cloud** — Expected. See Deployment Challenges above. Run locally or use the manual paste fallback.

**Frontend not loading** — Ensure backend is running on port 8000. Hard refresh with `Ctrl+Shift+R`.

---

## License

MIT — free to use, modify, and distribute.

---

*Built to explore RAG pipelines, LLM integration, and the real-world constraints of deploying AI tools that depend on third-party data sources.*
