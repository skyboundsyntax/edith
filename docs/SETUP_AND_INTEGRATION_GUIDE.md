# EDITH Platform: Setup, Architecture & Execution Guide

Welcome to **EDITH: Autonomous AI Data Intelligence Platform for Job Seekers**. This guide details the platform architecture, components, and local execution steps.

---

## 1. System Architecture Overview

The platform utilizes an event-driven, agentic architecture separated into three main layers:
* **Client Layer:** React 19 Single Page Application (Vite) providing the interactive career intelligence dashboard, data grid, trust meter badges, and provenance drawer.
* **Orchestration Layer:** FastAPI backend running LangGraph to manage the cyclic job discovery workflows, task states, REST APIs, and WebSockets.
* **Data & AI Layer:** Calibrated Job Trust Meter for mathematical legitimacy scoring, dynamic schema extraction, and TF-IDF cosine vector deduplication.

---

## 2. Core Components

### 2.1. LangGraph Agent Workflow
LangGraph manages the state machine for the data pipeline:
* **State Definition:** Strongly typed Pydantic `WorkflowState` containing `user_prompt`, `target_schema`, `pending_urls`, `raw_documents`, `processed_data`, `deduplicated_data`, and `execution_logs`.
* **Node 1: Intent Parser:** Converts the natural-language prompt into a typed `JobOpening` schema with role, skills, location, and compensation parameters.
* **Node 2: Source Discovery:** Executes real-time multi-portal scraping across LinkedIn Guest Search, Jobicy, and Arbeitnow, fetching live HTML/text.
* **Node 3: Data Extraction:** Extracts structured entities (job title, company, location, skills, experience, salary, direct apply link) and computes the 4-part Trust Meter score.
* **Node 4: RAG Deduplication:** Eliminates cross-portal duplicate listings using SHA-256 entity hashing and TF-IDF cosine similarity.
* **Node 5: Human Review Evaluation:** Flags listings with trust scores below the user-configured confidence threshold.

### 2.2. Backend Infrastructure
* **API Gateway:** FastAPI serving REST endpoints (`/api/workflows`, `/api/datasets`, `/api/export`, `/api/health`) and WebSockets (`/ws/workflows/{workflow_id}`) for real-time task monitoring.
* **Database Schema (SQLite / SQLAlchemy):**
  * `workflows`: Tracks workflow history, status (running, completed, failed), execution logs, and origin prompts.
  * `data_records`: Stores extracted JSON payloads, trust meter confidence scores, breakdown metrics, origin URL metadata, and timestamps.

---

## 3. Data Lineage & Traceability

To ensure all data is source-backed, the backend explicitly binds a `metadata` dictionary to every discovered document during the scraping phase. This metadata (`source_url`, `timestamp`, `raw_snippet`, `apply_link`) is persisted in the database, mapping directly to the frontend data tables and the interactive provenance audit drawer.

---

## 4. Configuration & Environment Settings

Create a `.env` file in the root directory (copied from [`.env.example`](file:///c:/Users/samat/Downloads/edith/.env.example)):

```bash
# --- Application Settings ---
PROJECT_NAME="EDITH - Autonomous Job Intelligence Platform"
VERSION="1.0.0"

# --- Database ---
DATABASE_URL="sqlite:///./data_intelligence.db"

# --- Optional Search & LLM Keys ---
TAVILY_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=

# --- Server Ports & URLs ---
PORT=8000
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

---

## 5. How to Run the Platform (Step-by-Step)

### Step 5.1: Launch FastAPI Backend
In the project root directory:

```powershell
py -3 -m uvicorn backend.main:app --port 8000
```
- **Backend API Gateway:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Diagnostics:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
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
1. Type a career search prompt into the input (e.g. *"Find active React developer jobs in Bangalore"*).
2. Watch the LangGraph state machine execute live via WebSockets.
3. Review extracted entities populated in the Dynamic Data Grid with genuine Jev Trust Meter scores.
4. Click **Inspect** on any row to open the **Data Lineage & Traceability** drawer (view origin URL, timestamp, raw snippet citation, and confidence breakdown).
5. Click **CSV** or **JSON** to download the clean dataset.
