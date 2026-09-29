import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import FirefliesBackground from './components/FirefliesBackground';
import Sidebar from './components/Sidebar';
import TopNavbar from './components/TopNavbar';
import JobCardList from './components/JobCardList';
import SalaryIntelligenceWidget from './components/SalaryIntelligenceWidget';
import FloatingCommandBar from './components/FloatingCommandBar';
import MetricsCards from './components/MetricsCards';
import WorkflowGraph from './components/WorkflowGraph';
import DataGrid from './components/DataGrid';
import SourceDrawer from './components/SourceDrawer';
import WorkflowHistoryModal from './components/WorkflowHistoryModal';
import SourceHealthModal from './components/SourceHealthModal';
import CandidateProfileModal from './components/CandidateProfileModal';
import { api } from './services/api';
import { Award, ShieldCheck, Sparkles, Activity } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [prompt, setPrompt] = useState('Find entry-level Python & AI/ML engineer roles in Pune or Bangalore or Remote, 0-2 years experience, minimum ₹6 LPA');
  const [searchTerm, setSearchTerm] = useState('');
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
  const [userProfile, setUserProfile] = useState(null);

  const socketRef = useRef(null);

  // Load User Profile on mount
  useEffect(() => {
    api.getUserProfile()
      .then((data) => {
        if (data?.profile) setUserProfile(data.profile);
      })
      .catch((err) => console.error('Error fetching user profile:', err));
  }, []);

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

  const handleLaunchWorkflow = async (promptText) => {
    const query = promptText || prompt;
    if (!query.trim() || isRunning) return;

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

  // Filter records by search term across title, company, location, skills
  const filteredRecords = useMemo(() => {
    if (!searchTerm.trim()) return records;
    const term = searchTerm.toLowerCase();
    return records.filter((r) => {
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
  }, [records, searchTerm]);

  return (
    <div className="edith-dashboard-layout">
      {/* 1. Animated Fireflies Particle Layer (Backdrop) */}
      <FirefliesBackground />

      {/* 2. Left Glassmorphic Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onOpenSourceHealth={() => setIsSourceHealthOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
        onOpenHistory={() => setIsHistoryOpen(true)}
        sourceCount={8}
      />

      {/* 3. Main Viewport */}
      <div className="edith-main-viewport">
        {/* Top Navbar */}
        <TopNavbar
          title={activeTab === 'jobs' ? 'Scraped Openings' : activeTab === 'analytics' ? 'Pipeline Analytics' : 'Dashboard'}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onOpenProfile={() => setIsProfileOpen(true)}
          onOpenSourceHealth={() => setIsSourceHealthOpen(true)}
          onExport={handleExport}
          isExporting={isExporting}
          unreadCount={records.length > 0 ? 1 : 0}
          userName={userProfile?.name ? userProfile.name.toUpperCase() : 'ALEX R.'}
          filteredCount={filteredRecords.length}
          totalCount={records.length}
        />

        {/* Dashboard Main Grid View */}
        {activeTab === 'dashboard' && (
          <div className="edith-dashboard-grid">
            {/* Center Jobs Feed */}
            <section className="edith-center-feed">
              {/* If pipeline is currently running, show live state tracker */}
              {isRunning && (
                <div style={{ marginBottom: '0.5rem' }}>
                  <WorkflowGraph
                    currentNode={currentNode}
                    status="running"
                    logs={executionLogs}
                  />
                </div>
              )}

              {/* Frosted Floating Job Cards with SVG Wave Sparklines */}
              <JobCardList
                records={filteredRecords}
                onInspectProvenance={(id) => setInspectRecordId(id)}
              />

              {/* Bottom Floating Command Bar: "Ask EDITH: ..." */}
              <FloatingCommandBar
                onLaunchPrompt={handleLaunchWorkflow}
                isRunning={isRunning}
                initialPrompt={prompt}
              />
            </section>

            {/* Right Column: Salary Intelligence Widget & Trust Metrics */}
            <aside className="edith-right-column">
              <SalaryIntelligenceWidget records={records} />

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

      <CandidateProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        onProfileUpdated={(updated) => setUserProfile(updated)}
      />
    </div>
  );
}
