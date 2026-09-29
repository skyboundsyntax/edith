import React from 'react';
import {
  LayoutGrid,
  User,
  Users,
  BarChart3,
  Settings,
  Activity,
  Layers
} from 'lucide-react';

export default function Sidebar({
  activeTab = 'dashboard',
  onSelectTab,
  onOpenSourceHealth,
  onOpenProfile,
  onOpenHistory,
  sourceCount = 8
}) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutGrid },
    { id: 'jobs', label: 'My Roles', icon: User },
    { id: 'network', label: 'Network', icon: Users, onClick: onOpenSourceHealth },
    { id: 'analytics', label: 'Insights', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings, onClick: onOpenProfile }
  ];

  return (
    <aside className="edith-sidebar">
      {/* Brand Header matching screenshot */}
      <div className="sidebar-brand">
        <div className="brand-emblem-box">
          <span className="brand-emblem-letter">E</span>
        </div>
        <div className="brand-text">
          <span className="brand-name">EDITH</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              aria-current={isActive ? 'page' : undefined}
              onClick={() => {
                if (item.onClick) {
                  item.onClick();
                } else if (onSelectTab) {
                  onSelectTab(item.id);
                }
              }}
            >
              <div className="nav-icon-wrap">
                <Icon size={19} />
              </div>
              <span className="nav-label">{item.label}</span>
              {isActive && <div className="nav-active-glow-indicator" />}
            </button>
          );
        })}
      </nav>

      {/* Sleek Minimal Footer matching clean screenshot aesthetic */}
      <div className="sidebar-footer">
        <button
          type="button"
          className="sidebar-status-pill"
          onClick={onOpenSourceHealth}
          title="Click to view 8 verified ATS connectors"
        >
          <div className="status-indicator-dot">
            <span className="ping-ring" />
            <span className="core-dot" />
          </div>
          <span className="status-pill-text">{sourceCount} Sources Live</span>
        </button>

        <button
          type="button"
          className="sidebar-history-icon-btn"
          onClick={onOpenHistory}
          title="View Search & Pipeline Runs"
          aria-label="Pipeline Runs"
        >
          <Layers size={16} />
        </button>
      </div>
    </aside>
  );
}
