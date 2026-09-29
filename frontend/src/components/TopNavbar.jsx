import React from 'react';
import { Search, X, Bell } from 'lucide-react';

/**
 * Top Navbar
 * Exactly reproduces the top floating pill/capsule from the reference screenshot:
 * Features a single continuous frosted glass container with glowing cyan borders,
 * left-aligned quick filter/search, and right-aligned notification bell with red dot,
 * circular user badge (A.R.), and search icon.
 */
export default function TopNavbar({
  searchTerm = '',
  onSearchChange,
  onOpenProfile,
  onOpenSourceHealth,
  unreadCount = 1,
  userName = 'A.R.'
}) {
  return (
    <header className="edith-top-navbar glass-panel-glow">
      {/* Search Input Area */}
      <div className="topbar-search-area">
        <input
          type="text"
          className="topbar-search-input"
          placeholder="Filter live scraped jobs by keyword, company, or tech stack..."
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

      {/* Right Controls matching screenshot */}
      <div className="topbar-right-controls">
        {/* Notification Bell with red badge */}
        <button
          type="button"
          className="topbar-icon-btn"
          onClick={onOpenSourceHealth}
          title="Notifications & Source telemetry"
          aria-label="Notifications"
        >
          <Bell size={18} />
          {unreadCount > 0 && <span className="topbar-notif-dot" />}
        </button>

        {/* User Badge: A.R. circle */}
        <button
          type="button"
          className="topbar-user-badge"
          onClick={onOpenProfile}
          title="Candidate Profile"
          aria-label="User profile"
        >
          <span>{userName || 'A.R.'}</span>
        </button>

        {/* Search Icon */}
        <button
          type="button"
          className="topbar-icon-btn search-trigger"
          title="Execute search"
          aria-label="Search"
        >
          <Search size={18} />
        </button>
      </div>
    </header>
  );
}
