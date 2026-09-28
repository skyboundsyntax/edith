import React from 'react';
import { BrainCircuit, Search, Cpu, GitMerge, Terminal, CheckCircle2 } from 'lucide-react';

const SDD_NODES = [
  {
    id: 'intent_parser',
    title: 'Node 1: Intent Parser',
    desc: 'Role & Stack Intent (Pydantic)',
    icon: BrainCircuit
  },
  {
    id: 'source_discovery',
    title: 'Node 2: Multi-Portal Scraper',
    desc: 'LinkedIn • Naukri • Indeed Crawl',
    icon: Search
  },
  {
    id: 'data_extraction',
    title: 'Node 3: Jev Trust Meter',
    desc: 'Anti-Ghost & CTC Calibrator',
    icon: Cpu
  },
  {
    id: 'vector_deduplication',
    title: 'Node 4: Cross-Platform Dedup',
    desc: 'Vector Similarity Pruning',
    icon: GitMerge
  }
];

export default function WorkflowGraph({
  currentNode = 'initialized',
  status = 'pending',
  logs = []
}) {
  const getNodeState = (nodeId, index) => {
    if (status === 'completed') return 'completed';
    if (currentNode === nodeId) return 'active';
    
    const currentIndex = SDD_NODES.findIndex((n) => n.id === currentNode);
    if (currentIndex > index) return 'completed';
    return 'idle';
  };

  return (
    <div className="glass-panel workflow-graph-section">
      <div className="graph-header">
        <h2>
          <BrainCircuit size={20} color="var(--accent-cyan)" />
          <span>Autonomous Job Scraping & Verification Pipeline</span>
        </h2>
        <div className="status-badge" style={{ textTransform: 'capitalize' }}>
          <span className="pulse-dot"></span>
          <span>Scraper Pipeline: {status}</span>
        </div>
      </div>

      {/* Visual Node Flow Track */}
      <div className="node-flow-track">
        <div className="flow-connector-line"></div>
        {SDD_NODES.map((node, idx) => {
          const state = getNodeState(node.id, idx);
          const Icon = node.icon;

          return (
            <div key={node.id} className={`agent-node ${state}`}>
              <div className="node-bubble">
                <Icon size={24} />
              </div>
              <div className="node-title">{node.title}</div>
              <div className="node-desc">{node.desc}</div>
            </div>
          );
        })}
      </div>

      {/* Real-time Telemetry Terminal */}
      <div className="telemetry-terminal">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem', color: 'var(--text-muted)' }}>
          <Terminal size={14} />
          <span style={{ fontSize: '0.725rem', letterSpacing: '0.05em' }}>LIVE AGENT TELEMETRY & STATE LOG</span>
        </div>
        {logs.length === 0 ? (
          <div className="log-line">
            <span className="log-time">--:--:--</span>
            <span className="log-msg" style={{ color: 'var(--text-muted)' }}>Awaiting prompt execution to launch LangGraph cycle...</span>
          </div>
        ) : (
          logs.slice(-6).map((log, i) => (
            <div key={i} className="log-line">
              <span className="log-time">
                {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}
              </span>
              <span className="log-node">[{log.node || 'agent'}]</span>
              <span className="log-msg">{log.message || JSON.stringify(log)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
