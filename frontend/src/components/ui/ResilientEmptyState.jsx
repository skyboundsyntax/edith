import React from 'react';
import { MapPin, Search, RefreshCw, Zap } from 'lucide-react';
import Butterfly from './Butterfly';

/**
 * Resilient Empty State Component
 * Handles boundary conditions gracefully with clear corrective actions.
 */
export default function ResilientEmptyState({
  filterType = 'ALL',
  searchTerm = '',
  onResetFilters,
  onTriggerScrape,
  isRunning = false
}) {
  const locationLabels = {
    PUNE: 'Pune',
    BLR: 'Bengaluru',
    MUM: 'Mumbai',
    DEL: 'Delhi NCR',
    HYD: 'Hyderabad',
    REMOTE: 'Remote / Online',
    OFFLINE: 'Offline / On-Site'
  };
  const activeLocLabel = locationLabels[filterType];

  let title = 'No Matching Openings Found';
  let desc = 'No job vacancies currently match your query criteria or active filter.';

  if (activeLocLabel) {
    title = `No Openings in ${activeLocLabel} in Current Snapshot`;
    desc = `The current dataset does not have vacancies in ${activeLocLabel}. You can launch a live real-time scrape across genuine ATS portals right now.`;
  } else if (searchTerm) {
    title = `No Results for "${searchTerm}"`;
    desc = 'Try adjusting your search keywords, role names, or resetting the location filter.';
  }

  return (
    <div
      className="resilient-empty-card glass-panel"
      role="status"
      aria-live="polite"
      style={{
        padding: '3rem 2rem',
        textAlign: 'center',
        borderRadius: '20px',
        background: 'rgba(11, 22, 40, 0.65)',
        border: '1.5px dashed rgba(86, 204, 242, 0.45)',
        backdropFilter: 'blur(25px)',
        margin: '1.5rem 0',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '1rem'
      }}
    >
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: activeLocLabel ? 'rgba(56, 189, 248, 0.15)' : 'rgba(56, 189, 248, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid rgba(56, 189, 248, 0.35)'
        }}
      >
        {activeLocLabel ? (
          <MapPin size={26} color="#38bdf8" />
        ) : (
          <Butterfly size={28} color="#38bdf8" />
        )}
      </div>

      <div style={{ maxWidth: '520px' }}>
        <h3
          style={{
            fontSize: '1.25rem',
            fontWeight: 800,
            color: '#ffffff',
            margin: '0 0 0.5rem 0',
            fontFamily: 'var(--font-display)'
          }}
        >
          {title}
        </h3>
        <p
          style={{
            fontSize: '0.875rem',
            color: '#94a3b8',
            lineHeight: 1.55,
            margin: 0
          }}
        >
          {desc}
        </p>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          flexWrap: 'wrap',
          justifyContent: 'center',
          marginTop: '0.5rem'
        }}
      >
        {onTriggerScrape && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={onTriggerScrape}
            disabled={isRunning}
            style={{
              background: 'linear-gradient(135deg, #0284c7, #0369a1)',
              color: '#ffffff',
              fontWeight: 700,
              padding: '0.65rem 1.25rem',
              borderRadius: '12px',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              boxShadow: '0 0 20px rgba(56, 189, 248, 0.35)'
            }}
          >
            <Zap size={16} />
            <span>{isRunning ? 'Scraping Live Portals...' : `⚡ Scrape Real-Time ${activeLocLabel ? activeLocLabel + ' ' : ''}Jobs Now`}</span>
          </button>
        )}

        {onResetFilters && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onResetFilters}
            style={{
              padding: '0.65rem 1.15rem',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              fontSize: '0.85rem'
            }}
          >
            <RefreshCw size={14} />
            <span>Reset All Filters</span>
          </button>
        )}
      </div>
    </div>
  );
}
