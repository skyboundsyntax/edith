import React from 'react';
import { Briefcase, Download, Layers, Activity } from 'lucide-react';

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
            <Briefcase size={22} color="var(--accent-cyan)" />
          </div>
          <div>
            <div className="brand-title">EDITH CAREERS</div>
            <div className="brand-tagline">Autonomous Job Intelligence • Web Scraper (LinkedIn • Naukri • Indeed) • Jev's Trust Meter</div>
          </div>
        </div>

        <div className="header-actions">
          {/* Live Orchestration Engine Status */}
          <div className="status-badge" title="FastAPI & LangGraph Job Scraper Active">
            <span className="pulse-dot"></span>
            <Activity size={14} />
            <span>Scraper Engine: Live</span>
          </div>

          {/* Workflow History */}
          <button className="btn btn-secondary" onClick={onOpenHistory} title="View Past Job Scrape Runs">
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
            <span>{isExporting ? 'Exporting...' : 'Export Jobs (CSV)'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
