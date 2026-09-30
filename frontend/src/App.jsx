import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import FirefliesBackground from './components/FirefliesBackground';
import Sidebar from './components/Sidebar';
import TopNavbar from './components/TopNavbar';
import HeroJobCard from './components/HeroJobCard';
import JobCardList from './components/JobCardList';
import SalaryIntelligenceWidget from './components/SalaryIntelligenceWidget';
import SkillDemandWidget from './components/SkillDemandWidget';
import FloatingCommandBar from './components/FloatingCommandBar';
import MetricsCards from './components/MetricsCards';
import WorkflowGraph from './components/WorkflowGraph';
import DataGrid from './components/DataGrid';
import SourceDrawer from './components/SourceDrawer';
import WorkflowHistoryModal from './components/WorkflowHistoryModal';
import SourceHealthModal from './components/SourceHealthModal';
import { api } from './services/api';
import { Award, ShieldCheck, Activity, Play, Sliders, LayoutGrid, List, CheckCircle2, AlertCircle } from 'lucide-react';
import { sanitizeSearchQuery } from './utils/urlValidator';
import { extractSalaryQuery, matchesSalaryBracket } from './utils/currencyFormatter';
import {
  LocationFilterBar,
  SalaryBracketFilterBar,
  Butterfly,
  isJobInPune,
  isJobInBengaluru,
  isJobInMumbai,
  isJobInDelhiNCR,
  isJobInHyderabad,
  isJobOnlineRemote,
  isJobOfflineOnSite,
  ResilientEmptyState,
  OfflineAlert
} from './components/ui';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error('EDITH Dashboard Error Caught:', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2.5rem',
          margin: '2rem',
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '16px',
          backdropFilter: 'blur(20px)',
          color: '#fca5a5'
        }}>
          <h3 style={{ margin: '0 0 0.75rem 0', color: '#f87171' }}>⚠️ Dashboard Component Render Error</h3>
          <p style={{ margin: '0 0 1.25rem 0', color: '#cbd5e1', fontSize: '0.9rem' }}>
            {this.state.error?.message || 'An unexpected rendering error occurred.'}
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
            >
              🔄 Retry & Reload Dashboard
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Dismiss & Recover View
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const PRESET_PROMPTS = [
  'Python Backend & AI Engineer Jobs across India (₹12-25 LPA)',
  'Active Python Backend & FastAPI Roles (Remote / Bangalore, ₹12-25 LPA)',
  'React 19 & Full Stack Openings across LinkedIn & ATS boards (₹10-22 LPA)',
  'Generative AI, PyTorch & LLM Systems Engineer Jobs (₹35-70 LPA / Remote)',
  'Fresher & SDE-1 Engineering Jobs across India (₹6-12 LPA)',
  'DevOps, Kubernetes & Cloud Architecture Vacancies (₹18-35 LPA)'
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardViewMode, setDashboardViewMode] = useState('cards');
  const [prompt, setPrompt] = useState('Find Python, AI/ML, Full Stack & Backend Engineer jobs in India, ₹12-30 LPA');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeLocationFilter, setActiveLocationFilter] = useState('ALL');
  const [activeSalaryBracket, setActiveSalaryBracket] = useState('ALL');
  const [networkError, setNetworkError] = useState(null);
  const [isRetryingConnection, setIsRetryingConnection] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState(75.0);
  const [isRunning, setIsRunning] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type });
    const timer = setTimeout(() => {
      setToast((prev) => (prev?.message === message ? null : prev));
    }, 4500);
    return () => clearTimeout(timer);
  }, []);

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
  const [isLoadingInitial, setIsLoadingInitial] = useState(true);

  const socketRef = useRef(null);

  const selectWorkflow = useCallback(async (workflowId) => {
    try {
      const details = await api.getWorkflowDetails(workflowId);
      if (details?.workflow) {
        setActiveWorkflow(details.workflow);
        setExecutionLogs(details.workflow.execution_logs || []);
        setCurrentNode('human_review_evaluation');
        setMetrics({
          total_extracted: details.workflow.total_extracted,
          total_deduplicated: details.workflow.total_deduplicated,
          duplicates_pruned: details.workflow.duplicates_pruned,
          human_review_count: details.workflow.human_review_count
        });
      }

      // Load records
      const datasetRes = await api.getDatasets({ workflow_id: workflowId });
      setRecords(datasetRes?.records || []);
    } catch (err) {
      console.error('Failed to select workflow:', err);
    } finally {
      setIsLoadingInitial(false);
    }
  }, []);

  const loadWorkflows = useCallback(async () => {
    try {
      const data = await api.getWorkflows();
      setWorkflows(data);
      if (data.length > 0 && !activeWorkflow) {
        const best = data.find((w) => (w.total_deduplicated || 0) > 0) || data[0];
        await selectWorkflow(best.id);
      }
    } catch (err) {
      console.error('Failed to load workflows:', err);
    } finally {
      setIsLoadingInitial(false);
    }
  }, [activeWorkflow, selectWorkflow]);

  // Initial load
  useEffect(() => {
    let ignore = false;
    api.getWorkflows()
      .then(async (data) => {
        if (!ignore) {
          setWorkflows(data);
          if (data.length > 0) {
            const best = data.find((w) => (w.total_deduplicated || 0) > 0) || data[0];
            await selectWorkflow(best.id);
          }
          setIsLoadingInitial(false);
        }
      })
      .catch((err) => {
        console.error('Failed to load workflows:', err);
        if (!ignore) setIsLoadingInitial(false);
      });
    return () => { ignore = true; };
  }, [selectWorkflow]);

  // Online / Offline resilience listeners
  useEffect(() => {
    const handleOnline = () => {
      setNetworkError(null);
      showToast('Network connection re-established. Live streams active.', 'success');
      loadWorkflows();
    };
    const handleOffline = () => {
      setNetworkError('Network connectivity lost. Operating in cached view until connection restores.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [loadWorkflows, showToast]);

  const handleRetryConnection = useCallback(async () => {
    setIsRetryingConnection(true);
    try {
      await loadWorkflows();
      setNetworkError(null);
    } catch (err) {
      setNetworkError(err?.message || 'Unable to establish connection to EDITH backend daemon.');
    } finally {
      setIsRetryingConnection(false);
    }
  }, [loadWorkflows]);

  const handleScrapeLive = () => {
    handleLaunchWorkflow(prompt);
  };

  const handleLaunchWorkflow = async (promptText) => {
    const query = promptText || prompt;
    if (!query.trim() || isRunning) return;

    // Auto-sync location filter based on prompt content:
    // If a specific city is specified, sync to that city; otherwise default to All India & Remote
    const qLower = query.toLowerCase();
    if (qLower.includes('pune') || qLower.includes('hinjewadi') || qLower.includes('kharadi') || qLower.includes('baner')) {
      setActiveLocationFilter('PUNE');
    } else if (qLower.includes('bangalore') || qLower.includes('bengaluru')) {
      setActiveLocationFilter('BLR');
    } else if (qLower.includes('mumbai')) {
      setActiveLocationFilter('MUM');
    } else if (qLower.includes('delhi') || qLower.includes('noida') || qLower.includes('gurgaon')) {
      setActiveLocationFilter('DEL');
    } else if (qLower.includes('hyderabad')) {
      setActiveLocationFilter('HYD');
    } else {
      setActiveLocationFilter('ALL');
    }

    // Auto-sync salary filter if query specifies a bracket
    const salCheck = extractSalaryQuery(query);
    if (salCheck.hasSalaryFilter) {
      if (salCheck.minLpa >= 30 && (salCheck.maxLpa === null || salCheck.maxLpa <= 45)) {
        setActiveSalaryBracket('30-40');
      } else if (salCheck.minLpa >= 20 && salCheck.maxLpa <= 30) {
        setActiveSalaryBracket('20-30');
      } else if (salCheck.minLpa >= 12 && salCheck.maxLpa <= 20) {
        setActiveSalaryBracket('12-20');
      } else if (salCheck.minLpa >= 6 && salCheck.maxLpa <= 12) {
        setActiveSalaryBracket('6-12');
      } else if (salCheck.minLpa >= 40) {
        setActiveSalaryBracket('40+');
      }
    }

    setPrompt(query);
    setIsRunning(true);
    setCurrentNode('query_planning');
    setExecutionLogs([{
      timestamp: new Date().toISOString(),
      node: 'query_planning',
      message: `Analyzing query and dispatching multi-source ATS connectors...`
    }]);

    try {
      const newWf = await api.createWorkflow(query, confidenceThreshold, null);
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
          // Socket error fallback
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
      setNetworkError(err?.message || 'Workflow execution failed. Verify connection.');
      showToast(`Scrape pipeline error: ${err.message}`, 'error');
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
      showToast(`Dataset exported successfully as ${res.filename} (${res.record_count} records)`, 'success');
    } catch (err) {
      showToast(`Export failed: ${err.message}`, 'error');
    } finally {
      setIsExporting(false);
    }
  };

  // Query-driven salary bracket detection
  const cleanSearch = useMemo(() => sanitizeSearchQuery(searchTerm).trim(), [searchTerm]);
  const detectedQueryBracket = useMemo(() => extractSalaryQuery(cleanSearch), [cleanSearch]);

  // Filter records by strict location selection, salary bracket, AND search terms
  const filteredRecords = useMemo(() => {
    let result = records || [];

    // 1. Strict Geographic / Modality filter
    if (activeLocationFilter === 'PUNE') {
      result = result.filter(isJobInPune);
    } else if (activeLocationFilter === 'BLR') {
      result = result.filter(isJobInBengaluru);
    } else if (activeLocationFilter === 'MUM') {
      result = result.filter(isJobInMumbai);
    } else if (activeLocationFilter === 'DEL') {
      result = result.filter(isJobInDelhiNCR);
    } else if (activeLocationFilter === 'HYD') {
      result = result.filter(isJobInHyderabad);
    } else if (activeLocationFilter === 'REMOTE') {
      result = result.filter(isJobOnlineRemote);
    } else if (activeLocationFilter === 'OFFLINE') {
      result = result.filter(isJobOfflineOnSite);
    }

    // 2. Strict Salary bracket filter:
    // Only show desired jobs in salary bracket and other jobs with unlisted salaries,
    // discard/hide any job with listed salary outside bracket.
    let effectiveMinLpa = null;
    let effectiveMaxLpa = null;

    if (detectedQueryBracket.hasSalaryFilter) {
      effectiveMinLpa = detectedQueryBracket.minLpa;
      effectiveMaxLpa = detectedQueryBracket.maxLpa;
    } else if (activeSalaryBracket !== 'ALL') {
      if (activeSalaryBracket === '6-12') { effectiveMinLpa = 6; effectiveMaxLpa = 12; }
      else if (activeSalaryBracket === '12-20') { effectiveMinLpa = 12; effectiveMaxLpa = 20; }
      else if (activeSalaryBracket === '20-30') { effectiveMinLpa = 20; effectiveMaxLpa = 30; }
      else if (activeSalaryBracket === '30-40') { effectiveMinLpa = 30; effectiveMaxLpa = 40; }
      else if (activeSalaryBracket === '40+') { effectiveMinLpa = 40; effectiveMaxLpa = null; }
    }

    if (effectiveMinLpa !== null || effectiveMaxLpa !== null) {
      result = result.filter((r) => {
        const d = r.data || {};
        const sal = d.salary_range || d.salary || '';
        return matchesSalaryBracket(sal, effectiveMinLpa, effectiveMaxLpa);
      });
    }

    // 3. Search term filter across title, company, location, skills, modality
    const remainingText = detectedQueryBracket.hasSalaryFilter
      ? detectedQueryBracket.remainingQuery
      : cleanSearch;

    if (!remainingText) return result;
    const term = remainingText.toLowerCase();

    return result.filter((r) => {
      const d = r.data || {};
      const title = String(d.job_title || '').toLowerCase();
      const comp = String(d.company || '').toLowerCase();
      const loc = String(d.location || '').toLowerCase();
      const skills = Array.isArray(d.skills) ? d.skills.join(' ').toLowerCase() : String(d.skills || '').toLowerCase();
      const modality = String(d.work_modality || '').toLowerCase();

      return title.includes(term) ||
        comp.includes(term) ||
        loc.includes(term) ||
        skills.includes(term) ||
        modality.includes(term);
    });
  }, [records, activeLocationFilter, cleanSearch, detectedQueryBracket, activeSalaryBracket]);

  // Hero Job Selection & Paging
  const [showSecondaryStream, setShowSecondaryStream] = useState(false);

  const currentHeroIndex = useMemo(() => {
    if (!filteredRecords.length) return 0;
    const idx = filteredRecords.findIndex((r) => r.id === selectedJobId);
    return idx >= 0 ? idx : 0;
  }, [filteredRecords, selectedJobId]);

  const activeHeroJob = filteredRecords[currentHeroIndex] || null;

  const handlePrevJob = () => {
    if (!filteredRecords.length) return;
    const nextIdx = (currentHeroIndex - 1 + filteredRecords.length) % filteredRecords.length;
    setSelectedJobId(filteredRecords[nextIdx].id);
  };

  const handleNextJob = () => {
    if (!filteredRecords.length) return;
    const nextIdx = (currentHeroIndex + 1) % filteredRecords.length;
    setSelectedJobId(filteredRecords[nextIdx].id);
  };

  return (
    <div className="edith-dashboard-layout">
      {/* 1. Animated Bokeh Background Layer with Ambient Blur */}
      <FirefliesBackground />

      {/* 2. Left Glassmorphic Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onOpenSourceHealth={() => setIsSourceHealthOpen(true)}
        onOpenHistory={() => setIsHistoryOpen(true)}
        sourceCount={7}
      />

      {/* 3. Main Viewport */}
      <div className="edith-main-viewport">
        {/* Top Navbar */}
        <TopNavbar
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onOpenSourceHealth={() => setIsSourceHealthOpen(true)}
          onExport={handleExport}
          isExporting={isExporting}
          unreadCount={records.length > 0 ? 1 : 0}
          totalCount={records.length}
        />

        {/* Main Content with ErrorBoundary */}
        <ErrorBoundary>
        {/* Dashboard Main Grid View */}
        {(activeTab === 'dashboard' || (!['jobs', 'analytics'].includes(activeTab))) && (
          <div className="edith-dashboard-grid">
            {/* Center Jobs Feed */}
            <section className="edith-center-feed">
              {/* Network Error / Offline Recovery Alert */}
              <OfflineAlert
                error={networkError}
                onRetry={handleRetryConnection}
                onDismiss={() => setNetworkError(null)}
                isRetrying={isRetryingConnection}
              />

              {/* 1. Real-time Pipeline Metrics Row */}
              <MetricsCards metrics={metrics} activeWorkflow={activeWorkflow} records={records} />

              {/* 2. Live Scraper Controls & Template Presets */}
              <section className="glass-panel hero-prompt-section" style={{ marginTop: '1rem', padding: '1.25rem 1.5rem', borderRadius: '16px' }}>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleLaunchWorkflow(prompt);
                  }}
                >
                  <div className="prompt-input-container">
                    <input
                      type="text"
                      className="prompt-input"
                      placeholder="Enter target role, tech stack, or location (e.g. 'Python & AI Engineer jobs in Pune, minimum ₹8 LPA')..."
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      disabled={isRunning}
                    />
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={isRunning || !prompt.trim()}
                      style={{ padding: '0.65rem 1.35rem', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '0.45rem', fontWeight: 700 }}
                    >
                      <Play size={15} fill="white" />
                      <span>{isRunning ? 'Scraping Portals...' : 'Scrape Real Jobs'}</span>
                    </button>
                  </div>

                  {/* Prompt Presets */}
                  <div className="prompt-presets" style={{ marginTop: '0.85rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>QUICK CAREER TEMPLATES:</span>
                    {PRESET_PROMPTS.map((p, i) => (
                      <button
                        key={i}
                        type="button"
                        className="preset-pill"
                        onClick={() => {
                          setPrompt(p);
                          handleLaunchWorkflow(p);
                        }}
                        disabled={isRunning}
                      >
                        {p}
                      </button>
                    ))}
                  </div>

                  {/* Threshold Slider Controls */}
                  <div className="prompt-controls-row" style={{ marginTop: '0.75rem' }}>
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

              {/* 3. LangGraph Pipeline State Machine Visualizer */}
              <div style={{ marginTop: '1rem' }}>
                <WorkflowGraph
                  currentNode={currentNode}
                  status={isRunning ? 'running' : activeWorkflow?.status || 'completed'}
                  logs={executionLogs}
                />
              </div>

              {/* 4. Tactile Geographic & Modality Location Filter Bar */}
              <LocationFilterBar
                activeFilter={activeLocationFilter}
                onSelectFilter={setActiveLocationFilter}
                records={records}
                onScrapePune={handleScrapeLive}
                isRunning={isRunning}
              />

              {/* 4b. Strict Salary Bracket Filter Bar */}
              <SalaryBracketFilterBar
                activeBracket={activeSalaryBracket}
                onSelectBracket={setActiveSalaryBracket}
                detectedQueryBracket={detectedQueryBracket}
                onClearQueryBracket={() => {
                  if (detectedQueryBracket.hasSalaryFilter) {
                    setSearchTerm(detectedQueryBracket.remainingQuery);
                  }
                }}
              />

              {/* 5. Verified Openings Header with View Mode Switcher */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginTop: '1rem',
                marginBottom: '1rem',
                padding: '0.25rem 0.25rem'
              }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Butterfly size={19} color="var(--accent-amber)" />
                    <span>Real-Time Scraped Openings</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                      ({filteredRecords.length} Active Positions{activeLocationFilter !== 'ALL' ? ` in ${activeLocationFilter}` : ''}{activeSalaryBracket !== 'ALL' && !detectedQueryBracket.hasSalaryFilter ? ` • ₹${activeSalaryBracket} LPA` : detectedQueryBracket.hasSalaryFilter ? ` • Query ₹${detectedQueryBracket.minLpa}${detectedQueryBracket.maxLpa ? `-${detectedQueryBracket.maxLpa}` : '+'} LPA` : ''})
                    </span>
                  </h3>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <button
                    type="button"
                    className={`btn ${dashboardViewMode === 'cards' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.785rem', padding: '0.4rem 0.85rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                    onClick={() => setDashboardViewMode('cards')}
                    title="Interactive Cards & Hero View"
                  >
                    <LayoutGrid size={14} />
                    <span>Cards View</span>
                  </button>
                  <button
                    type="button"
                    className={`btn ${dashboardViewMode === 'table' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.785rem', padding: '0.4rem 0.85rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                    onClick={() => setDashboardViewMode('table')}
                    title="Full Table Data Grid View"
                  >
                    <List size={14} />
                    <span>Table View</span>
                  </button>
                </div>
              </div>

              {/* 6. Main Jobs Presentation */}
              {dashboardViewMode === 'cards' ? (
                isLoadingInitial ? (
                  <div className="glass-panel" style={{ padding: '3.5rem 2rem', textAlign: 'center', borderRadius: '18px', background: 'rgba(13, 23, 42, 0.65)' }}>
                    <div className="status-indicator-dot" style={{ margin: '0 auto 1.25rem auto', width: '14px', height: '14px' }}>
                      <span className="ping-ring" style={{ background: '#38bdf8' }} />
                      <span className="core-dot" style={{ width: '8px', height: '8px', background: '#38bdf8' }} />
                    </div>
                    <h3 style={{ margin: '0 0 0.5rem 0', color: '#f8fafc', fontSize: '1.15rem', fontWeight: 600 }}>Connecting to Live Job Ingestion Stream</h3>
                    <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.85rem' }}>Aggregating deterministic postings from Greenhouse, Lever, Ashby, LinkedIn, and Arbeitnow...</p>
                  </div>
                ) : filteredRecords.length === 0 ? (
                  <ResilientEmptyState
                    filterType={activeLocationFilter}
                    searchTerm={searchTerm}
                    onResetFilters={() => {
                      setActiveLocationFilter('ALL');
                      setSearchTerm('');
                    }}
                    onTriggerScrape={() => handleLaunchWorkflow()}
                    isRunning={isRunning}
                  />
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Hero Featured Job Card */}
                    <HeroJobCard
                      job={activeHeroJob}
                      currentIndex={currentHeroIndex}
                      totalCount={filteredRecords.length}
                      onPrevJob={handlePrevJob}
                      onNextJob={handleNextJob}
                      onInspectProvenance={(id) => setInspectRecordId(id)}
                      onTriggerScrape={() => handleLaunchWorkflow()}
                    />

                    {/* Complete Stream of All Other Verified Openings (DIRECTLY VISIBLE!) */}
                    {filteredRecords.length > 1 && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginTop: '0.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 0.5rem' }}>
                          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            All Verified Opportunities ({filteredRecords.length})
                          </span>
                          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                            Direct Apply • Anti-Ghost Audited
                          </span>
                        </div>
                        <JobCardList
                          records={filteredRecords}
                          onInspectProvenance={(id) => setInspectRecordId(id)}
                          onToggleExpand={(id) => setSelectedJobId(id)}
                          expandedId={selectedJobId}
                        />
                      </div>
                    )}
                  </div>
                )
              ) : (
                /* Table Grid View */
                <DataGrid
                  records={filteredRecords}
                  schema={activeWorkflow?.target_schema}
                  onInspectProvenance={(id) => setInspectRecordId(id)}
                  onExport={handleExport}
                  isExporting={isExporting}
                />
              )}

              {/* 6. Bottom Floating Command Bar */}
              <FloatingCommandBar
                onLaunchPrompt={handleLaunchWorkflow}
                isRunning={isRunning}
                initialPrompt={prompt}
              />
            </section>

            {/* Right Column: Salary Intelligence Widget & Skill Demand Trend & Trust Badge */}
            <aside className="edith-right-column">
              <SalaryIntelligenceWidget records={records} />
              <SkillDemandWidget records={records} />

              {/* Jev's Anti-Ghost Trust Badge Card */}
              <div className="glass-panel" style={{ padding: '1.25rem', background: 'rgba(13, 23, 42, 0.58)', backdropFilter: 'blur(20px)', borderRadius: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
                  <ShieldCheck size={18} color="var(--accent-cyan)" />
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>
                    Jev's Trust & Anti-Ghost Verifier
                  </span>
                </div>
                <p style={{ fontSize: '0.785rem', color: '#94a3b8', lineHeight: 1.45, margin: 0 }}>
                  Every extracted role is verified through canonical robots compliance and cryptographic domain lineage before appearing on your feed.
                </p>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <span style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600 }}>
                    ✓ 100% Genuine Direct Postings
                  </span>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem' }}
                    onClick={() => setIsSourceHealthOpen(true)}
                  >
                    View Matrix
                  </button>
                </div>
              </div>
            </aside>
          </div>
        )}

        {/* Detailed Full-Table Jobs View */}
        {activeTab === 'jobs' && (
          <div style={{ padding: '1rem 2.25rem 4rem 2.25rem' }}>
            <DataGrid
              records={filteredRecords}
              schema={activeWorkflow?.target_schema}
              onInspectProvenance={(id) => setInspectRecordId(id)}
              onExport={handleExport}
              isExporting={isExporting}
            />
          </div>
        )}

        {/* Analytics & Pipeline View */}
        {activeTab === 'analytics' && (
          <div style={{ padding: '1rem 2.25rem 4rem 2.25rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <MetricsCards metrics={metrics} activeWorkflow={activeWorkflow} records={records} />
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 360px', gap: '1.5rem' }}>
              <WorkflowGraph
                currentNode={currentNode}
                status={isRunning ? 'running' : activeWorkflow?.status || 'idle'}
                logs={executionLogs}
              />
              <SalaryIntelligenceWidget records={records} />
            </div>
          </div>
        )}
        </ErrorBoundary>
      </div>

      {/* Modals & Drawers */}
      <SourceDrawer
        recordId={inspectRecordId}
        onClose={() => setInspectRecordId(null)}
        onRecordUpdated={() => selectWorkflow(activeWorkflow?.id)}
      />

      <WorkflowHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        workflows={workflows}
        activeWorkflowId={activeWorkflow?.id}
        onSelectWorkflow={(id) => selectWorkflow(id)}
      />

      <SourceHealthModal
        isOpen={isSourceHealthOpen}
        onClose={() => setIsSourceHealthOpen(false)}
      />

      {/* Non-blocking Resilience Toast Dock */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem',
            padding: '0.85rem 1.25rem',
            borderRadius: '12px',
            backdropFilter: 'blur(24px)',
            boxShadow: '0 10px 40px rgba(0,0,0,0.5)',
            border: toast.type === 'error' ? '1px solid rgba(239, 68, 68, 0.4)' : toast.type === 'success' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(56, 189, 248, 0.4)',
            background: toast.type === 'error' ? 'rgba(30, 10, 15, 0.92)' : toast.type === 'success' ? 'rgba(6, 30, 20, 0.92)' : 'rgba(8, 24, 40, 0.92)',
            color: toast.type === 'error' ? '#fca5a5' : toast.type === 'success' ? '#6ee7b7' : '#bae6fd',
            fontSize: '0.85rem',
            fontWeight: 500,
            maxWidth: '420px',
            animation: 'fadeInUp 0.25s ease-out'
          }}
        >
          {toast.type === 'error' ? (
            <AlertCircle size={18} color="#f87171" style={{ flexShrink: 0 }} />
          ) : (
            <CheckCircle2 size={18} color="#34d399" style={{ flexShrink: 0 }} />
          )}
          <span style={{ flex: 1 }}>{toast.message}</span>
          <button
            type="button"
            onClick={() => setToast(null)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              padding: '0 4px',
              fontSize: '1rem',
              lineHeight: 1
            }}
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
