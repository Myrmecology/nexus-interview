# ⬡ NEXUS INTERVIEW

> An AI-powered system design interview simulator built with Python and Claude AI.
> Practice FAANG-level architecture challenges with real-time intelligent pushback,
> dynamic follow-up questions, and detailed performance scoring.

---

## ⚡ Live Demo

![Nexus Interview Screenshot](https://via.placeholder.com/900x500/080b0f/00ffe0?text=NEXUS+INTERVIEW)

---

## 🧠 What Is This?

Nexus Interview is a full-stack AI application that simulates a real system design
interview with a senior FAANG engineer. You are given a challenge — like designing
a URL shortener or YouTube's upload pipeline — and an AI interviewer named **Nexus**
pushes back on your answers, probes your weak spots, and scores your performance
across three dimensions: scalability, reliability, and communication.

The entire experience runs in the browser with no installs required.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────┐
│                   Browser                    │
│         HTML + CSS + Vanilla JS              │
│   Boot Screen → Chat UI → Score Panel        │
└──────────────────┬──────────────────────────┘
                   │ HTTP / Streaming
┌──────────────────▼──────────────────────────┐
│              FastAPI Backend                 │
│         Python 3.11 — Uvicorn ASGI           │
│                                              │
│  /api/interview/start   → Start session      │
│  /api/interview/chat    → Stream response    │
│  /api/interview/hint    → Get a nudge        │
│  /api/interview/score   → Score session      │
└──────────────────┬──────────────────────────┘
                   │ Anthropic SDK
┌──────────────────▼──────────────────────────┐
│              Claude Sonnet 4                 │
│     System prompt → Conversation history     │
│     Streaming SSE → Structured JSON scoring  │
└─────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Why |
|---|---|---|
| AI Engine | Claude Sonnet 4 (Anthropic) | Best in class reasoning and instruction following |
| Backend | FastAPI + Uvicorn | Async-first, fast, automatic API docs |
| Data Validation | Pydantic v2 | Type-safe request and response schemas |
| Frontend | HTML + CSS + Vanilla JS | Zero build toolchain, ships instantly |
| Testing | Pytest + pytest-cov | Clean unit and integration coverage |
| Environment | python-dotenv | Secure secrets management |

---

## 🔑 Key Engineering Decisions

### Why Streaming Instead of Batch Responses?

The single biggest UX decision in this project was choosing **Server-Sent streaming**
over standard JSON responses for the chat endpoint. A batch response makes the user
stare at a blank screen for 3-5 seconds. Streaming delivers the first token in
under 500ms and makes the interviewer feel alive and human — like it is genuinely
thinking through your answer in real time. On YouTube, the difference between these
two approaches is the difference between a boring demo and a jaw-dropping one.

### Why In-Memory Sessions Instead of a Database?

For a demo-scale application, introducing a database like PostgreSQL or Redis would
add infrastructure complexity with zero user-facing benefit. Sessions are stored in
a Python dictionary keyed by UUID. The tradeoff is that sessions reset on server
restart — an acceptable limitation for a local demo that a persistent store would
over-engineer. If this were a production SaaS product, the session dictionary would
be swapped for Redis with a TTL, a one-line change in `claude_service.py`.

### Why a Structured JSON Scoring Prompt?

Getting Claude to return consistent, parseable scores required careful prompt
engineering. Early versions returned scores embedded in conversational prose — 
unparseable and inconsistent. The solution was a strict system prompt that demands
a specific JSON schema and nothing else, combined with a `json.loads()` parse step
that throws immediately if the contract is violated. This forced Claude to be
deterministic rather than creative at scoring time.

### Why Vanilla JS Instead of React?

React would add a build pipeline, node_modules, and deployment complexity for a
frontend that is fundamentally a chat window with three buttons. Vanilla JS keeps
the entire frontend as three files — zero dependencies, zero build step, opens
directly from disk. The streaming reader, the boot sequence, and the score renderer
are all achievable in under 300 lines of clean JavaScript.

---

## 📁 Project Structure

```
nexus-interview/
├── backend/
│   ├── main.py              # App entry point and middleware
│   ├── config.py            # Environment and settings
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   ├── routes/
│   │   └── interview.py     # All API endpoints
│   └── services/
│       └── claude_service.py # Claude API brain
├── frontend/
│   ├── index.html           # Single page application shell
│   ├── css/
│   │   └── style.css        # Terminal brutalism design system
│   └── js/
│       └── app.js           # All UI logic and streaming
├── tests/
│   ├── test_services.py     # Unit tests for Claude service
│   └── test_routes.py       # Integration tests for API routes
├── .env.example             # Environment variable template
├── .gitignore               # Security-hardened ignore rules
├── requirements.txt         # Pinned Python dependencies
└── README.md                # You are here
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Myrmecology/nexus-interview.git
cd nexus-interview
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your_key_here
```

Get your API key at [console.anthropic.com](https://console.anthropic.com)

### 5. Run the application

```bash
python -m backend.main
```

Open your browser at **http://127.0.0.1:8000**

---

## 🧪 Running Tests

```bash
pytest tests/ -v --cov=backend --cov-report=term-missing
```

---

## 🎯 Interview Questions Bank

| Difficulty | Questions |
|---|---|
| Beginner | URL Shortener, Rate Limiter, Parking Lot, Cache System |
| Intermediate | Notification System, Ride Sharing, News Feed, Chat System |
| Advanced | YouTube Upload Pipeline, Twitter Trending, Job Scheduler, CDN |

---

## 💡 How It Works

1. **You select a difficulty** and optionally specify a topic
2. **Nexus opens the interview** with a system design challenge
3. **You respond** — Nexus pushes back with targeted follow-up questions
4. **Use HINT** if you get stuck — Nexus nudges without giving the answer
5. **Hit SCORE ME** — Nexus reviews the full conversation and scores you
6. **Review your evaluation** — scalability, reliability, communication scores
   with specific strengths and areas to improve

---

## 🔒 Security

- API keys stored in `.env` — never committed to version control
- `.gitignore` hardened for YubiKey, GPG, and hardware security tokens
- No user data persisted — all sessions exist only in memory
- CORS configured to localhost only in development

---

## 🗺 Roadmap

- [ ] Persistent session history with SQLite
- [ ] User accounts and score tracking over time
- [ ] Voice input and text-to-speech responses
- [ ] Custom question submission
- [ ] Exportable PDF score reports

---

## 📄 License

MIT License 

---

> Built with Python, FastAPI, and Claude AI.
> Designed for engineers who want to get better.


