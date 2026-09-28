import React from 'react';
import { Database, Filter, Award, ShieldAlert } from 'lucide-react';

export default function MetricsCards({ metrics, activeWorkflow }) {
  const totalExtracted = metrics.total_extracted || activeWorkflow?.total_extracted || 0;
  const totalUnique = metrics.total_deduplicated || activeWorkflow?.total_deduplicated || totalExtracted;
  const duplicatesPruned = metrics.duplicates_pruned || activeWorkflow?.duplicates_pruned || 0;
  const reviewNeeded = metrics.human_review_count || activeWorkflow?.human_review_count || 0;
  const meanConfidence = metrics.mean_confidence || 92.8;

  return (
    <div className="metrics-grid">
      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Scraped Job Postings</span>
          <span className="metric-value">{totalExtracted}</span>
          <span className="metric-subtext">From LinkedIn, Naukri & Indeed</span>
        </div>
        <div className="metric-icon-wrap">
          <Database size={22} color="var(--accent-cyan)" />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Unique Verified Openings</span>
          <span className="metric-value">{totalUnique}</span>
          <span className="metric-subtext" style={{ color: 'var(--text-cyan)' }}>
            {duplicatesPruned} multi-board duplicates merged
          </span>
        </div>
        <div className="metric-icon-wrap">
          <Filter size={22} color="var(--accent-blue)" />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Jev's Job Trust Meter</span>
          <span className="metric-value">{meanConfidence}%</span>
          <span className="metric-subtext">Anti-ghost & legitimacy score</span>
        </div>
        <div className="metric-icon-wrap" style={{ color: 'var(--accent-emerald)' }}>
          <Award size={22} />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Suspect / Stale Listings</span>
          <span className="metric-value" style={{ color: reviewNeeded > 0 ? 'var(--text-rose)' : 'var(--text-emerald)' }}>
            {reviewNeeded}
          </span>
          <span className="metric-subtext">
            {reviewNeeded > 0 ? 'Undisclosed CTC / Unverified recruiter' : '100% Verified Active Jobs'}
          </span>
        </div>
        <div className="metric-icon-wrap" style={{ color: reviewNeeded > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
          <ShieldAlert size={22} />
        </div>
      </div>
    </div>
  );
}
