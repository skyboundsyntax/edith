import React from 'react';
import {
  LayoutDashboard,
  FolderGit2,
  TrendingUp,
  CircleDollarSign,
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
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'jobs', label: 'Scraped Jobs', icon: FolderGit2 },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'sources', label: 'Sources', icon: CircleDollarSign, onClick: onOpenSourceHealth },
    { id: 'settings', label: 'Settings', icon: Settings, onClick: onOpenProfile }
  ];

  return (
    <aside className="edith-sidebar">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div className="brand-logo-symbol">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="edithBrandGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="50%" stopColor="#0ea5e9" />
                <stop offset="100%" stopColor="#6366f1" />
              </linearGradient>
              <filter id="brandGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>
            {/* Geometric stylized 'E' matching the screenshot */}
            <path
              d="M7 6H25C25.5 6 26 6.5 26 7V10C26 10.5 25.5 11 25 11H13V14H22C22.5 14 23 14.5 23 15V17C23 17.5 22.5 18 22 18H13V21H25C25.5 21 26 21.5 26 22V25C26 25.5 25.5 26 25 26H7C6.4 26 6 25.6 6 25V7C6 6.4 6.4 6 7 6Z"
              fill="url(#edithBrandGrad)"
              filter="url(#brandGlow)"
            />
            {/* Sleek layered accent bars */}
            <path d="M10 9H23" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
            <path d="M10 16H20" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
            <path d="M10 23H23" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
          </svg>
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

      {/* Footer System Status */}
      <div className="sidebar-footer">
        <button
          type="button"
          className="sidebar-status-card"
          onClick={onOpenSourceHealth}
          title="Click to view all 8 verified ATS and public job connectors"
        >
          <div className="status-indicator-dot">
            <span className="ping-ring" />
            <span className="core-dot" />
          </div>
          <div className="status-info">
            <div className="status-title">Live Connectors</div>
            <div className="status-subtitle">{sourceCount} Verified Sources</div>
          </div>
          <Activity size={14} className="status-arrow-icon" />
        </button>

        <button
          type="button"
          className="sidebar-history-btn"
          onClick={onOpenHistory}
          title="View Search & Pipeline History"
        >
          <Layers size={15} />
          <span>Pipeline Runs</span>
        </button>
      </div>
    </aside>
  );
}
