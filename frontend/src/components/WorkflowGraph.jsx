import React from 'react';
import { BrainCircuit, Search, Cpu, GitMerge, Terminal, Activity } from 'lucide-react';

const EDITH_NODES = [
  {
    id: 'intent_parsing',
    title: 'Stage 1: Intent Parsing',
    desc: 'Semantic Intent & Schema Planning',
    icon: BrainCircuit,
    aliases: ['query_planning', 'intent_parser']
  },
  {
    id: 'source_discovery',
    title: 'Stage 2: Source Discovery & Scraping',
    desc: 'Autonomous Web & API Ingestion',
    icon: Search,
    aliases: ['source_connectors']
  },
  {
    id: 'extraction_mapping',
    title: 'Stage 3: Extraction & Schema Mapping',
    desc: 'Target Entity Extraction & Normalization',
    icon: Cpu,
    aliases: ['normalization', 'data_extraction']
  },
  {
    id: 'deduplication_scoring',
    title: 'Stage 4: Deduplication & Trust Scoring',
    desc: 'Exact/Cosine Deduplication & Semantic Trust Scoring',
    icon: GitMerge,
    aliases: ['deduplication', 'match_scoring', 'human_review_evaluation', 'vector_deduplication']
  }
];

export default function WorkflowGraph({
  currentNode = 'initialized',
  status = 'pending',
  logs = []
}) {
  const getNodeState = (node, index) => {
    if (status === 'completed') return 'completed';
    if (currentNode === node.id || (node.aliases && node.aliases.includes(currentNode))) return 'active';
    
    const currentIndex = EDITH_NODES.findIndex((n) => n.id === currentNode || (n.aliases && n.aliases.includes(currentNode)));
    if (currentIndex > index) return 'completed';
    return 'idle';
  };

  const safeLogs = Array.isArray(logs) ? logs : [];

  return (
    <div className="glass-panel workflow-graph-section">
      <div className="graph-header">
        <h2>
          <BrainCircuit size={20} color="var(--accent-amber)" />
          <span>Autonomous Data Intelligence & Extraction Pipeline</span>
        </h2>
        <div className="status-badge" style={{ textTransform: 'capitalize' }}>
          <span className="pulse-dot"></span>
          <span>Pipeline: {status}</span>
        </div>
      </div>

      {/* Visual Dynamic Node Flow Track */}
      <div className="node-flow-track">
        <div className="flow-connector-line"></div>
        {EDITH_NODES.map((node, idx) => {
          const state = getNodeState(node, idx);
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
        {safeLogs.length === 0 ? (
          <div className="log-line">
            <span className="log-time">{new Date().toLocaleTimeString()}</span>
            <span className="log-node">[telemetry]</span>
            <span className="log-msg" style={{ color: 'var(--text-muted)' }}>
              Live agent stream active. Listening for real-time LangGraph execution events...
            </span>
          </div>
        ) : (
          safeLogs.slice(-8).map((log, i) => {
            if (!log) return null;
            let timeStr = '--:--:--';
            try {
              timeStr = log?.timestamp ? new Date(log.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
            } catch {
              timeStr = new Date().toLocaleTimeString();
            }
            const nodeStr = typeof log === 'object' && log?.node ? log.node : 'pipeline';
            const msgStr = typeof log === 'object' && log?.message ? log.message : (typeof log === 'string' ? log : JSON.stringify(log));

            return (
              <div key={i} className="log-line">
                <span className="log-time">{timeStr}</span>
                <span className="log-node">[{nodeStr}]</span>
                <span className="log-msg">{msgStr}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
