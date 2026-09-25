# EDITH Platform: Setup, SDD Architecture & Execution Guide

Welcome to the **AI-Powered Data Intelligence Platform** (`EDITH`). This guide details the platform architecture strictly implementing the **Software Design Document (SDD 1.0)** and **Product Requirements Document (PRD 1.0)**.

---

## 1. System Architecture Overview (SDD Section 1)

The platform utilizes an event-driven, agentic architecture separated into three main layers:
* **Client Layer:** Next.js / React Single Page Application (SPA) providing the centralized dashboard.
* **Orchestration Layer:** FastAPI backend running LangGraph to manage the cyclic data-collection workflows and task states.
* **Data & AI Layer:** TypeSafe AI's Jev model for deterministic extraction, standard LLMs (OpenAI/Anthropic/Gemini) for intent parsing, and Qdrant/Milvus for vector-based RAG deduplication.

---

## 2. Core Components (SDD Section 2)

### 2.1. LangGraph Agent Workflow
LangGraph manages the state machine for the data pipeline:
* **State Definition:** `Dict[str, Any]` containing `user_prompt`, `target_schema`, `pending_urls`, `processed_data`, and `error_logs`.
* **Node 1: Intent Parser (Standard LLM):** Converts the natural-language prompt into a structured JSON schema (Pydantic model) outlining required fields.
* **Node 2: Source Discovery:** Calls a search API (e.g., Tavily / live web search) to gather a list of permitted URLs based on the intent.
* **Node 3: Data Extraction (Jev Model):** Takes raw HTML/Markdown from scraping tools and the target schema. Jev returns strictly typed values and a mathematically calibrated confidence score.
* **Node 4: RAG Deduplication:** Embeds the newly extracted entity and queries the Vector DB. If a similarity threshold is met, Jev evaluates the two records to confirm duplication.

### 2.2. Backend Infrastructure
* **API Gateway:** FastAPI serving REST endpoints (`/api/workflows`, `/api/datasets`, `/api/export`) and WebSockets (`/ws/workflows/{workflow_id}`) for real-time task monitoring.
* **Database Schema (PostgreSQL / SQLite):**
  * `Workflows`: Tracks workflow history, status (running, completed, failed), execution logs, and origin prompts.
  * `DataRecords`: Stores the extracted JSON payloads, Jev confidence scores, confidence breakdown, and origin URL metadata.

---

## 3. Data Lineage & Traceability (SDD Section 3)

To ensure all data is source-backed, the backend explicitly binds a `metadata` dictionary to every LangChain `Document` object during the scraping phase. This metadata (`source_url`, `timestamp`, `raw_snippet`) is passed through Jev and persisted in the database, mapping directly to the frontend data tables and the interactive provenance audit drawer.

---

## 4. Configuration & Environment Settings

Create a `.env` file in the root directory (copied from [`.env.example`](file:///c:/Users/samat/Downloads/edith/.env.example)):

```bash
# --- Application Settings ---
PROJECT_NAME="AI-Powered Data Intelligence Platform"
VERSION="1.0.0"

# --- Database Schema (SDD Section 2.2) ---
# Default SQLite local database. For production PostgreSQL (Supabase/Neon), replace with:
# DATABASE_URL=postgresql://user:password@localhost:5432/edith_db
DATABASE_URL="sqlite:///./data_intelligence.db"

# --- Autonomous Search & AI Keys (SDD Section 2.1) ---
TAVILY_API_KEY=your_tavily_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
TYPESAFE_JEV_API_KEY=your_typesafe_jev_key_here

# --- Server Ports & URLs ---
PORT=8000
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

---

## 5. How to Run the Platform (Step-by-Step)

### Step 5.1: Launch FastAPI Backend & LangGraph Agent Engine
In the project root directory:

```powershell
py -3 -m uvicorn backend.main:app --reload --port 8000
```
- **Backend API Gateway:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Live Telemetry WebSocket:** `ws://localhost:8000/ws/live`

### Step 5.2: Launch Client Layer (React Dashboard)
In a separate terminal:

```powershell
cd frontend
npm run dev
```
- **Frontend Dashboard URL:** [http://localhost:5173](http://localhost:5173)

---

## 6. Verification and Exporting
1. Type a natural language requirement into the hero input (e.g. *"Find me AI engineers in Bangalore with PyTorch & LangGraph"*).
2. Watch the 4-stage LangGraph state machine execute live via WebSockets.
3. Review extracted entities populated in the Dynamic Data Grid with mathematical Jev confidence scores.
4. Click **Inspect** on any row to open the **Data Lineage & Traceability** drawer (view origin URL, timestamp, raw snippet citation, and confidence breakdown).
5. Click **Export Dataset** to download the clean CSV or JSON dataset.
