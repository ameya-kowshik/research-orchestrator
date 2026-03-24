# 🔬 Agentic Research Engine

A self-correcting AI research assistant built with LangGraph, FastAPI, and PostgreSQL. Give it any topic and it autonomously researches, critiques, and generates a structured report.

---

## How It Works

```
User Query → Planner → Researcher → Critic → (loop if needed) → Summarizer → Report
```

- **Planner** — analyzes the query and determines report structure
- **Researcher** — searches the web via Tavily
- **Critic** — validates results, sends back for refinement if needed (max 3 attempts)
- **Summarizer** — generates a structured report with sections and key takeaways

Live node updates are streamed to the UI via SSE as the agent works.

---

## Demo

**Query:** `"Compare React vs Vue for large-scale applications"`

```
✅ PLANNER     — Report type: comparison | Sections: Overview, Syntax, Performance, Ecosystem, Verdict
🔍 RESEARCHER  — Search #1
❌ CRITIC      — Requested revision: missing performance benchmarks
🔍 RESEARCHER  — Search #2
✅ CRITIC      — Approved
📝 SUMMARIZER  — Report generated
💾             — Saved to database
```

**Output:**
```
📊 React vs Vue for Large-Scale Applications

🔑 Key Takeaways
- React has a larger ecosystem and is preferred for complex SPAs
- Vue has a gentler learning curve and better two-way binding
- Both support TypeScript, but React's TS support is more mature
- ...

Overview       | Both are component-based JS frameworks...
Performance    | React uses a virtual DOM; Vue 3 uses a Proxy-based...
Ecosystem      | React: 200k+ GitHub stars, backed by Meta...
Verdict        | React for large teams; Vue for faster onboarding...
```

---

## Stack

| Layer | Tech |
|---|---|
| Agent | LangGraph + Gemini 2.5 Flash |
| Search | Tavily API |
| Backend | FastAPI + SSE |
| Database | PostgreSQL (Neon) + SQLAlchemy async |
| Frontend | Streamlit |

---

## Setup

**1. Clone and install**
```bash
pip install -r requirements.txt
```

**2. Configure `.env`**
```
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
```

**3. Run the API**
```bash
uvicorn app.main:app --reload
```

**4. Run the frontend**
```bash
streamlit run streamlit_app.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/research/stream` | Run research, stream SSE updates |
| GET | `/reports` | List all past reports |
| GET | `/reports/{id}` | Get a specific report |
