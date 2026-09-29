import React from 'react';
import { Briefcase, Download, Layers, Activity } from 'lucide-react';

export default function Header({
  onOpenHistory,
  onOpenSourceHealth,
  onOpenProfile,
  onExport,
  isExporting
}) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="brand-section">
          <div className="logo-icon">
            <Briefcase size={22} color="var(--accent-amber)" />
          </div>
          <div>
            <div className="brand-title">EDITH</div>
            <div className="brand-tagline">AI Job Intelligence • Multi-Source ATS Connectors • Explainable Match Scoring</div>
          </div>
        </div>

        <div className="header-actions">
          {/* Source Health Matrix */}
          <button
            type="button"
            className="status-badge"
            onClick={onOpenSourceHealth}
            title="View Real-Time Status & Robots Compliance across 8 Sources"
            style={{ cursor: 'pointer', border: '1px solid rgba(245, 158, 11, 0.3)' }}
          >
            <span className="pulse-dot"></span>
            <Activity size={14} />
            <span>Sources: Live (8)</span>
          </button>

          {/* Candidate Profile */}
          <button className="btn btn-secondary" onClick={onOpenProfile} title="Configure Job Seeker Candidate Profile">
            <span>Candidate Profile</span>
          </button>

          {/* Workflow History */}
          <button className="btn btn-secondary" onClick={onOpenHistory} title="View Past Job Intelligence Runs">
            <Layers size={16} />
            <span>Search History</span>
          </button>

          {/* Direct Dataset Export */}
          <button
            className="btn btn-primary"
            onClick={() => onExport('csv')}
            disabled={isExporting}
            title="Export Verified Jobs Dataset"
          >
            <Download size={16} />
            <span>{isExporting ? 'Exporting...' : 'Export (CSV)'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
