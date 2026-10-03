import React from 'react';
import { Search, X, Bell, Download, ShieldCheck, Activity } from 'lucide-react';

/**
 * Top Navbar
 * Frosted glass capsule with glowing cyan borders:
 * Left-aligned quick filter/search, and right-aligned notification bell,
 * source telemetry matrix button, and dataset export.
 */
export default function TopNavbar({
  searchTerm = '',
  onSearchChange,
  onOpenSourceHealth,
  onExport,
  isExporting = false,
  unreadCount = 1,
  totalCount = 0
}) {
  return (
    <header className="edith-top-navbar glass-panel-glow">
      {/* Search Input Area */}
      <div className="topbar-search-area">
        <Search size={16} color="var(--text-muted)" style={{ marginRight: '0.65rem' }} />
        <input
          type="text"
          className="topbar-search-input"
          placeholder="Filter verified jobs by role, technology (Python, React), company, or city..."
          value={searchTerm}
          onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
          aria-label="Search jobs"
        />
        {searchTerm && (
          <button
            type="button"
            className="topbar-clear-btn"
            onClick={() => onSearchChange && onSearchChange('')}
            title="Clear search"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Right Controls */}
      <div className="topbar-right-controls">
        {/* Source Matrix Status */}
        <button
          type="button"
          className="topbar-status-badge"
          onClick={onOpenSourceHealth}
          title="Click to view ATS Source Health & Anti-Ghost Matrix"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            background: 'rgba(56, 189, 248, 0.08)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            borderRadius: '999px',
            padding: '0.3rem 0.65rem',
            color: '#38bdf8',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
          <span>Live Sources</span>
        </button>

        {/* Quick Export CTA */}
        {onExport && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => onExport('csv')}
            disabled={isExporting}
            style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
            title="Export Scraped Jobs to CSV"
          >
            <Download size={13} />
            <span>{isExporting ? 'Exporting...' : 'Export'}</span>
          </button>
        )}

        {/* Notification Bell with red badge */}
        <button
          type="button"
          className="topbar-icon-btn"
          onClick={onOpenSourceHealth}
          title="Source Telemetry & Notifications"
          aria-label="Notifications"
        >
          <Bell size={17} />
          {unreadCount > 0 && <span className="topbar-notif-dot" />}
        </button>
      </div>
    </header>
  );
}

