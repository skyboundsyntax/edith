import React from 'react';
import { Search, X, Bell, ChevronDown, Download, Filter } from 'lucide-react';

export default function TopNavbar({
  title = 'Dashboard',
  searchTerm = '',
  onSearchChange,
  onOpenProfile,
  onOpenSourceHealth,
  onExport,
  isExporting,
  unreadCount = 1,
  userName = 'ALEX R.',
  filteredCount = 0,
  totalCount = 0
}) {
  return (
    <header className="edith-top-navbar">
      {/* Title */}
      <div className="navbar-left">
        <h1 className="page-title">{title}</h1>
      </div>

      {/* Centered Instant Filter Bar */}
      <div className="navbar-center">
        <div className="pill-search-container">
          <Filter size={16} className="pill-search-icon" />
          <input
            type="text"
            className="pill-search-input"
            placeholder="Quick filter loaded jobs by role, company, or skills..."
            value={searchTerm}
            onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
            aria-label="Filter loaded jobs by keyword"
          />

          {/* Result Count / Clear Button */}
          {searchTerm ? (
            <button
              type="button"
              className="pill-clear-btn"
              onClick={() => onSearchChange && onSearchChange('')}
              title="Clear filter"
              aria-label="Clear filter"
            >
              <X size={15} />
            </button>
          ) : (
            totalCount > 0 && (
              <span className="pill-count-tag" title="Total jobs loaded in current view">
                {totalCount} Openings
              </span>
            )
          )}
        </div>
      </div>

      {/* Right User Actions */}
      <div className="navbar-right">
        {/* Quick CSV Export */}
        {onExport && (
          <button
            type="button"
            className="navbar-action-btn export-pill"
            onClick={() => onExport('csv')}
            disabled={isExporting}
            title="Download CSV of current verified job records"
            aria-label="Export verified job dataset to CSV"
          >
            <Download size={15} />
            <span>{isExporting ? 'Exporting...' : 'Export'}</span>
          </button>
        )}

        {/* Notifications */}
        <button
          type="button"
          className="navbar-icon-btn notifications-btn"
          onClick={onOpenSourceHealth}
          title="Active telemetry notifications & source health"
          aria-label="Source health notifications"
        >
          <Bell size={18} />
          {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
        </button>

        {/* User Profile Pill */}
        <button
          type="button"
          className="navbar-user-pill"
          onClick={onOpenProfile}
          title="Click to configure candidate target profile & preferences"
          aria-label="Candidate profile settings"
        >
          <div className="user-avatar-circle">
            <span className="user-initials">
              {userName && userName.length >= 2 ? userName.slice(0, 2).toUpperCase() : 'AR'}
            </span>
          </div>
          <span className="user-name">{userName}</span>
          <ChevronDown size={14} className="user-dropdown-arrow" />
        </button>
      </div>
    </header>
  );
}
