import React, { useState, useEffect, useRef } from 'react';
import { Play, Sparkles, Sliders } from 'lucide-react';
import Header from './components/Header';
import MetricsCards from './components/MetricsCards';
import WorkflowGraph from './components/WorkflowGraph';
import DataGrid from './components/DataGrid';
import SourceDrawer from './components/SourceDrawer';
import WorkflowHistoryModal from './components/WorkflowHistoryModal';
import { api } from './services/api';

const PRESET_PROMPTS = [
  'Active Python Backend & FastAPI Roles (Remote / Bangalore, ₹25-45 LPA)',
  'React 19 & Full Stack Openings across LinkedIn, Naukri & Indeed',
  'Generative AI, PyTorch & LLM Systems Engineer Jobs ($120k+ / Remote)',
  'Fresher & 2024-2026 Batch Software Development Jobs & Internships',
  'DevOps, Kubernetes & Cloud Architecture Vacancies with Disclosed CTC'
];

export default function App() {
  const [prompt, setPrompt] = useState('Find active Full-Stack and Python Engineer job openings on LinkedIn, Naukri, and Indeed with salary, skills, and direct apply link');
  const [confidenceThreshold, setConfidenceThreshold] = useState(80.0);
  const [isRunning, setIsRunning] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // Workflow & State Data
  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [records, setRecords] = useState([]);
  const [currentNode, setCurrentNode] = useState('initialized');
  const [executionLogs, setExecutionLogs] = useState([]);
  const [metrics, setMetrics] = useState({});

  // Modals & Drawers
  const [inspectRecordId, setInspectRecordId] = useState(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const socketRef = useRef(null);

  // Initial load
  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const data = await api.getWorkflows();
      setWorkflows(data);
      if (data.length > 0 && !activeWorkflow) {
        selectWorkflow(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load workflows:', err);
    }
  };

  const selectWorkflow = async (workflowId) => {
    try {
      const details = await api.getWorkflowDetails(workflowId);
      setActiveWorkflow(details.workflow);
      setExecutionLogs(details.workflow.execution_logs || []);
      setCurrentNode('vector_deduplication');
      setMetrics({
        total_extracted: details.workflow.total_extracted,
        total_deduplicated: details.workflow.total_deduplicated,
        duplicates_pruned: details.workflow.duplicates_pruned,
        human_review_count: details.workflow.human_review_count
      });

      // Load records
      const datasetRes = await api.getDatasets({ workflow_id: workflowId });
      setRecords(datasetRes.records || []);
    } catch (err) {
      console.error('Failed to select workflow:', err);
    }
  };

  const handleLaunchWorkflow = async (e) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isRunning) return;

    setIsRunning(true);
    setCurrentNode('intent_parser');
    setExecutionLogs([{
      timestamp: new Date().toISOString(),
      node: 'intent_parser',
      message: `Initiating autonomous LangGraph workflow pipeline for prompt: "${prompt}"`
    }]);

    try {
      const newWf = await api.createWorkflow(prompt, confidenceThreshold);
      setActiveWorkflow(newWf);

      // Connect to WebSocket for live node streaming
      if (socketRef.current) {
        socketRef.current.close();
      }

      socketRef.current = api.connectWebSocket(
        newWf.id,
        (event) => {
          if (event.node) {
            setCurrentNode(event.node);
          }
          if (event.logs) {
            setExecutionLogs((prev) => [...prev, event.logs]);
          }
          if (event.type === 'WORKFLOW_COMPLETED') {
            setIsRunning(false);
            selectWorkflow(newWf.id);
            loadWorkflows();
          }
        },
        () => {
          // Fallback polling if WebSocket drops
          setTimeout(() => {
            selectWorkflow(newWf.id);
            setIsRunning(false);
          }, 4000);
        }
      );

      // Safety timeout
      setTimeout(() => {
        if (isRunning) {
          selectWorkflow(newWf.id);
          setIsRunning(false);
        }
      }, 7000);

    } catch (err) {
      alert(`Workflow execution failed: ${err.message}`);
      setIsRunning(false);
    }
  };

  const handleExport = async (format = 'csv') => {
    setIsExporting(true);
    try {
      const res = await api.exportDataset(format, activeWorkflow?.id);
      if (res.download_url) {
        window.open(res.download_url, '_blank');
      }
      alert(`Dataset exported successfully as ${res.filename} (${res.record_count} records)`);
    } catch (err) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <Header
        onOpenHistory={() => setIsHistoryOpen(true)}
        onExport={handleExport}
        isExporting={isExporting}
      />

      {/* Main Content Area */}
      <main className="main-content">
        {/* Hero Prompt Section */}
        <section className="glass-panel hero-prompt-section">
          <div className="hero-header">
            <div className="hero-title-group">
              <h1>Autonomous Job Intelligence & Career Scraping Engine</h1>
              <p>Live multi-platform web scraper targeting LinkedIn, Naukri, and Indeed with Jev's Trust Meter for anti-ghost & scam verification</p>
            </div>
          </div>

          {/* Prompt Form */}
          <form onSubmit={handleLaunchWorkflow} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="prompt-input-container">
              <Sparkles size={20} color="var(--accent-cyan)" style={{ marginRight: '0.75rem' }} />
              <input
                type="text"
                className="prompt-input"
                placeholder="Enter target role, tech stack, or location (e.g. 'Senior Python & FastAPI developer jobs remote with salary')..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isRunning}
              />
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isRunning || !prompt.trim()}
              >
                <Play size={16} fill="white" />
                <span>{isRunning ? 'Scraping Portals...' : 'Scrape Jobs'}</span>
              </button>
            </div>

            {/* Prompt Presets */}
            <div className="prompt-presets">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>QUICK CAREER TEMPLATES:</span>
              {PRESET_PROMPTS.map((p, i) => (
                <button
                  key={i}
                  type="button"
                  className="preset-pill"
                  onClick={() => setPrompt(p)}
                  disabled={isRunning}
                >
                  {p}
                </button>
              ))}
            </div>

            {/* Threshold Slider Controls */}
            <div className="prompt-controls-row">
              <div className="threshold-slider-group">
                <Sliders size={14} />
                <span>Jev Anti-Ghost Trust Threshold:</span>
                <input
                  type="range"
                  min="50"
                  max="95"
                  step="5"
                  className="threshold-slider"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                  disabled={isRunning}
                />
                <span style={{ fontWeight: 700, color: 'var(--text-cyan)', fontFamily: 'var(--font-mono)' }}>
                  {confidenceThreshold}%
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  (Flag job listings below {confidenceThreshold}% for unverified CTC, stale posting, or suspect recruiter)
                </span>
              </div>
            </div>
          </form>
        </section>

        {/* Real-time Metrics Row */}
        <MetricsCards metrics={metrics} activeWorkflow={activeWorkflow} />

        {/* LangGraph State Machine Visualizer (SDD Section 2.1) */}
        <WorkflowGraph
          currentNode={currentNode}
          status={isRunning ? 'running' : activeWorkflow?.status || 'idle'}
          logs={executionLogs}
        />

        {/* Dynamic Data Grid */}
        <DataGrid
          records={records}
          schema={activeWorkflow?.target_schema}
          onInspectProvenance={(id) => setInspectRecordId(id)}
          onExport={handleExport}
          isExporting={isExporting}
        />
      </main>

      {/* Source Provenance Audit Drawer (SDD Section 3) */}
      <SourceDrawer
        recordId={inspectRecordId}
        onClose={() => setInspectRecordId(null)}
        onRecordUpdated={() => selectWorkflow(activeWorkflow?.id)}
      />

      {/* Workflow History Drawer */}
      <WorkflowHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        workflows={workflows}
        activeWorkflowId={activeWorkflow?.id}
        onSelectWorkflow={(id) => selectWorkflow(id)}
      />
    </div>
  );
}
