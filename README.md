# EDITH | Autonomous AI Job Intelligence Platform

> **Translating natural-language career requirements into clean, structured, and source-backed job datasets with multi-portal web scraping, anti-ghost Trust Meter verification, and verifiable data lineage.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20State%20Machine-blue)](https://langchain-ai.github.io/langgraph/)
[![React 19](https://img.shields.io/badge/React%2019-Vite-61DAFB?logo=react&logoColor=black)](https://vitejs.dev)
[![Trust Meter](https://img.shields.io/badge/Legitimacy%20Audit-Jev's%20Trust%20Meter-10B981)](#)

---

## 🏛️ System Architecture Overview

```
edith/
├── backend/                 # Backend & AI Engine: FastAPI, LangGraph & Jev Pipeline
│   ├── ai_engine/           # Data & AI Layer: LangGraph & Deterministic Extraction
│   │   ├── intent_parser.py # Node 1: Dynamic JobOpening schema extraction from query
│   │   ├── source_discovery.py # Node 2: Multi-portal live scraping with Firecrawl & APIs
│   │   ├── jev_extractor.py # Node 3: Jev Deterministic Extraction & 4-pillar Trust Meter
│   │   ├── vector_deduplication.py # Node 4: TF-IDF & cosine vector similarity
│   │   ├── workflow_graph.py # LangGraph StateGraph agent pipeline
│   │   └── state.py         # Strongly typed WorkflowState contract
│   ├── app/
│   │   ├── api/             # REST Endpoints (/workflows, /datasets, /exports, /sources, /health)
│   │   ├── core/            # Configuration, environment loading, settings
│   │   ├── db/              # SQLAlchemy Database Models (workflows, data_records, jobs)
│   │   ├── intelligence/    # Query planner, role matcher, match scorer, orchestrator
│   │   ├── services/        # Firecrawl web scraper service & dataset export engine
│   │   ├── sources/         # Live connectors (Firecrawl, LinkedIn, Jobicy, Arbeitnow, etc.)
│   │   └── websocket/       # Bi-directional WebSocket real-time node streaming
│   ├── exports/             # Generated dataset downloads (CSV & JSON)
│   ├── scripts/             # Database inspection & maintenance utilities
│   ├── tests/               # Automated test suites
│   ├── data_intelligence.db # SQLite Database (persisted extracted job records)
│   ├── main.py              # Application entrypoint
│   └── requirements.txt     # Consolidated backend dependencies
├── frontend/                # Client Layer: React 19 + Vite Glassmorphic Dashboard
│   ├── src/
│   │   ├── components/      # DataGrid, WorkflowGraph, FirecrawlScrapeModal, Header, MetricsCards
│   │   ├── services/        # API client and WebSocket streaming manager
│   │   ├── index.css        # Rich Vanilla CSS Design System with dark mode & glow effects
│   │   └── App.jsx          # Master Dashboard application
│   └── package.json
├── docs/                    # Specifications and Audit Reports
├── start.bat                # One-click dual-stack startup script
└── .env.example             # Environment configuration template
```

---

## 🔄 Core LangGraph Agent Pipeline
1. **Node 1: Intent Parser:** Converts the natural-language prompt into a typed `JobOpening` schema with role, skills, location, and compensation parameters.
2. **Node 2: Source Discovery & Firecrawl Scraping:** Scrapes live job openings across Firecrawl (JS-rendered web scraping), LinkedIn Guest Search API, Jobicy Remote, and Arbeitnow, retrieving high-fidelity markdown and content.
3. **Node 3: Jev Deterministic Extraction & Anti-Ghost Trust Meter:** Extracts structured entities using Jev and calculates an honest 0–100% Trust Meter based on token grounding (35%), completeness (30%), apply URL integrity (20%), and information density (15%).
4. **Node 4: Semantic Deduplication:** Identifies and merges cross-board duplicate listings using SHA-256 entity hashing and TF-IDF cosine similarity.
5. **Node 5: Human Review Evaluation:** Automatically flags listings scoring below the threshold for review.

---

## 🚀 Quickstart

### Firecrawl API key
EDITH uses Firecrawl for web search and for scraping pages that need JavaScript rendering. Add a Firecrawl API key to the project-root `.env` file before starting the backend:

```dotenv
FIRECRAWL_API_KEY=your_firecrawl_api_key
FIRECRAWL_API_URL=https://api.firecrawl.dev
```

Get an API key from your Firecrawl account, then copy `.env.example` to `.env` and replace the placeholder value. Keep `.env` private and never commit your key.

The Firecrawl Search API is unavailable without a valid key. EDITH can still try its public job-board sources, and direct-URL scraping has a local fallback, but results may be limited when Firecrawl is not configured.

### Windows: One-click launch
Double-click `start.bat` from the project folder. It checks the Python backend, installs frontend dependencies from the lockfile if needed, starts both services, and opens the dashboard after both are responding.

### 1. Launch FastAPI Backend
```powershell
py -3 -m uvicorn backend.main:app --port 8000
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 2. Launch Client Layer (React Dashboard)
```powershell
cd frontend
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

## 🛡️ Data Lineage & Traceability
Every job record binds provenance metadata (`source_url`, `timestamp`, `raw_snippet`, `apply_link`) persisted in SQLite and surfaced in the frontend **Source Inspection Drawer**.