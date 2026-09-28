import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Sparkles, Sliders } from 'lucide-react';
import Header from './components/Header';
import MetricsCards from './components/MetricsCards';
import WorkflowGraph from './components/WorkflowGraph';
import DataGrid from './components/DataGrid';
import SourceDrawer from './components/SourceDrawer';
import WorkflowHistoryModal from './components/WorkflowHistoryModal';
import InterpretedRequirements from './components/InterpretedRequirements';
import SourceHealthModal from './components/SourceHealthModal';
import CandidateProfileModal from './components/CandidateProfileModal';
import { api } from './services/api';

const PRESET_PROMPTS = [
  'Entry-level Python & AI/ML engineer roles in Pune or Bangalore or Remote (₹6-18 LPA)',
  'Second-year CSE internships for Python, React, SQL & Machine Learning at startups',
  'Fresher Full-Stack & FastAPI Developer jobs with disclosed CTC in India',
  'Generative AI, PyTorch & LLM Systems Engineer Jobs in India or Remote',
  'DevOps, Kubernetes & Cloud Architecture Vacancies (0-2 years experience)'
];

export default function App() {
  const [prompt, setPrompt] = useState('Find entry-level Python & AI/ML engineer roles in Pune or Bangalore or Remote, 0-2 years experience, minimum ₹6 LPA');
  const [spec, setSpec] = useState(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState(75.0);
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
  const [isSourceHealthOpen, setIsSourceHealthOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const socketRef = useRef(null);

  const selectWorkflow = useCallback(async (workflowId) => {
    try {
      const details = await api.getWorkflowDetails(workflowId);
      setActiveWorkflow(details.workflow);
      setExecutionLogs(details.workflow.execution_logs || []);
      setCurrentNode('human_review_evaluation');
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
  }, []);

  const loadWorkflows = useCallback(async () => {
    try {
      const data = await api.getWorkflows();
      setWorkflows(data);
      if (data.length > 0 && !activeWorkflow) {
        selectWorkflow(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load workflows:', err);
    }
  }, [activeWorkflow, selectWorkflow]);

  // Initial load
  useEffect(() => {
    let ignore = false;
    api.getWorkflows()
      .then((data) => {
        if (!ignore) {
          setWorkflows(data);
          if (data.length > 0) {
            selectWorkflow(data[0].id);
          }
        }
      })
      .catch((err) => console.error('Failed to load workflows:', err));
    return () => { ignore = true; };
  }, [selectWorkflow]);

  // Automatically plan requirements when prompt changes (debounced)
  useEffect(() => {
    if (!prompt.trim()) return;
    let cancel = false;
    const timer = setTimeout(async () => {
      try {
        const planRes = await api.planRequirements(prompt);
        if (!cancel && planRes.spec) {
          setSpec(planRes.spec);
        }
      } catch (err) {
        console.error('Plan requirements error:', err);
      }
    }, 400);

    return () => {
      cancel = true;
      clearTimeout(timer);
    };
  }, [prompt]);

  const handleLaunchWorkflow = async (e) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isRunning) return;

    setIsRunning(true);
    setCurrentNode('query_planning');
    setExecutionLogs([{
      timestamp: new Date().toISOString(),
      node: 'query_planning',
      message: `Analyzing natural-language request and synthesizing search requirements...`
    }]);

    try {
      const newWf = await api.createWorkflow(prompt, confidenceThreshold, spec);
      setActiveWorkflow(newWf);

      // Connect to WebSocket for live pipeline telemetry
      if (socketRef.current) {
        socketRef.current.close();
      }

      let isFinished = false;

      socketRef.current = api.connectWebSocket(
        newWf.id,
        (event) => {
          const evType = event.event || event.type;
          let nodeKey = 'query_planning';

          if (evType === 'source_started' || evType === 'jobs_found' || evType === 'source_completed') {
            nodeKey = 'source_connectors';
          } else if (evType === 'normalization_completed') {
            nodeKey = 'normalization';
          } else if (evType === 'deduplication_completed') {
            nodeKey = 'deduplication';
          } else if (evType === 'validation_completed' || evType === 'scoring_completed') {
            nodeKey = 'match_scoring';
          }

          setCurrentNode(nodeKey);

          let logMsg = event.message;
          if (!logMsg) {
            if (evType === 'source_started') logMsg = `Connecting to ${event.source} (${event.domain})...`;
            else if (evType === 'jobs_found') logMsg = `${event.source}: Retrieved ${event.count} postings in ${event.duration_ms}ms.`;
            else if (evType === 'deduplication_completed') logMsg = `Deduplication: Pruned ${event.removed} duplicate listings.`;
            else if (evType === 'scoring_completed') logMsg = `Calculated explainable fit scores for ${event.count} listings.`;
            else logMsg = JSON.stringify(event);
          }

          setExecutionLogs((prev) => [
            ...prev,
            {
              timestamp: event.timestamp || new Date().toISOString(),
              node: nodeKey,
              message: logMsg
            }
          ]);

          if (event.type === 'WORKFLOW_COMPLETED' || evType === 'pipeline_completed') {
            isFinished = true;
            setIsRunning(false);
            selectWorkflow(newWf.id);
            loadWorkflows();
          }
        },
        () => {
          // Socket error handler
        }
      );

      // Resilient background poller
      const pollInterval = setInterval(async () => {
        if (isFinished) {
          clearInterval(pollInterval);
          return;
        }
        try {
          const check = await api.getWorkflowDetails(newWf.id);
          if (check?.workflow?.status === 'completed' || check?.workflow?.status === 'failed') {
            isFinished = true;
            clearInterval(pollInterval);
            setIsRunning(false);
            selectWorkflow(newWf.id);
            loadWorkflows();
          }
        } catch (pollErr) {
          console.error('Polling error:', pollErr);
        }
      }, 2000);

      setTimeout(() => {
        clearInterval(pollInterval);
        if (!isFinished) {
          selectWorkflow(newWf.id);
          setIsRunning(false);
        }
      }, 45000);

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
        onOpenSourceHealth={() => setIsSourceHealthOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
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
              <p>Live multi-platform web scraper targeting ATS boards, remote job feeds, and structured Link-Out searches with Jev's Trust Meter for anti-ghost & scam verification</p>
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

          {/* AI Interpreted Search Specification */}
          <InterpretedRequirements
            spec={spec}
            onUpdateSpec={setSpec}
            onLaunch={handleLaunchWorkflow}
            isRunning={isRunning}
          />
        </section>

        {/* Real-time Metrics Row */}
        <MetricsCards metrics={metrics} activeWorkflow={activeWorkflow} records={records} />

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

      {/* Source Health & Robots Compliance Modal */}
      <SourceHealthModal
        isOpen={isSourceHealthOpen}
        onClose={() => setIsSourceHealthOpen(false)}
      />

      {/* Candidate Profile Modal */}
      <CandidateProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
      />
    </div>
  );
}
