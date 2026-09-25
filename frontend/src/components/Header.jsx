import React from 'react';
import { Cpu, Download, Layers, Activity } from 'lucide-react';

export default function Header({
  onOpenHistory,
  onExport,
  isExporting,
  systemStatus
}) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="brand-section">
          <div className="logo-icon">
            <Cpu size={22} />
          </div>
          <div>
            <div className="brand-title">EDITH INTELLIGENCE</div>
            <div className="brand-tagline">Deterministic AI Agent • Source Traceability • LangGraph Engine</div>
          </div>
        </div>

        <div className="header-actions">
          {/* Live Orchestration Engine Status */}
          <div className="status-badge" title="FastAPI & LangGraph Engine Active">
            <span className="pulse-dot"></span>
            <Activity size={14} />
            <span>Agent Engine: Live</span>
          </div>

          {/* Workflow History */}
          <button className="btn btn-secondary" onClick={onOpenHistory} title="View Past Agent Runs">
            <Layers size={16} />
            <span>Workflow Runs</span>
          </button>

          {/* Direct Dataset Export */}
          <button
            className="btn btn-primary"
            onClick={() => onExport('csv')}
            disabled={isExporting}
            title="Export CSV Dataset"
          >
            <Download size={16} />
            <span>{isExporting ? 'Exporting...' : 'Export Dataset (CSV)'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
