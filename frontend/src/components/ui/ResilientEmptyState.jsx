import React from 'react';
import { Sparkles, MapPin, Search, RefreshCw, Zap } from 'lucide-react';

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
  const isPune = filterType === 'PUNE';

  let title = 'No Matching Openings Found';
  let desc = 'No job vacancies currently match your query criteria or active filter.';

  if (isPune) {
    title = 'No Openings in Pune in Current Snapshot';
    desc = 'The current dataset does not have vacancies in Pune tech hubs (Hinjewadi, Kharadi, Baner, Wakad). You can launch a live scrape specifically for Pune right now.';
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
          background: isPune ? 'rgba(245, 158, 11, 0.15)' : 'rgba(56, 189, 248, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: isPune ? '1px solid rgba(245, 158, 11, 0.35)' : '1px solid rgba(56, 189, 248, 0.35)'
        }}
      >
        {isPune ? (
          <MapPin size={26} color="#fbbf24" />
        ) : (
          <Sparkles size={26} color="#38bdf8" />
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
        {isPune && onTriggerScrape && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={onTriggerScrape}
            disabled={isRunning}
            style={{
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              color: '#000000',
              fontWeight: 800,
              padding: '0.65rem 1.25rem',
              borderRadius: '12px',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              boxShadow: '0 0 20px rgba(245, 158, 11, 0.45)'
            }}
          >
            <Zap size={16} />
            <span>{isRunning ? 'Scraping Pune Portals...' : '⚡ Scrape Real Pune Jobs Now'}</span>
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
