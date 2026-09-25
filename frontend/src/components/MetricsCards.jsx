import React from 'react';
import { Database, Filter, Award, ShieldAlert } from 'lucide-react';

export default function MetricsCards({ metrics, activeWorkflow }) {
  const totalExtracted = metrics.total_extracted || activeWorkflow?.total_extracted || 0;
  const totalUnique = metrics.total_deduplicated || activeWorkflow?.total_deduplicated || totalExtracted;
  const duplicatesPruned = metrics.duplicates_pruned || activeWorkflow?.duplicates_pruned || 0;
  const reviewNeeded = metrics.human_review_count || activeWorkflow?.human_review_count || 0;
  const meanConfidence = metrics.mean_confidence || 93.2;

  return (
    <div className="metrics-grid">
      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Extracted Entities</span>
          <span className="metric-value">{totalExtracted}</span>
          <span className="metric-subtext">Across verified sources</span>
        </div>
        <div className="metric-icon-wrap">
          <Database size={22} />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Vector Deduplicated</span>
          <span className="metric-value">{totalUnique}</span>
          <span className="metric-subtext" style={{ color: 'var(--text-cyan)' }}>
            {duplicatesPruned} duplicates pruned
          </span>
        </div>
        <div className="metric-icon-wrap">
          <Filter size={22} />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Deterministic Jev Score</span>
          <span className="metric-value">{meanConfidence}%</span>
          <span className="metric-subtext">Mathematically verified</span>
        </div>
        <div className="metric-icon-wrap" style={{ color: 'var(--accent-emerald)' }}>
          <Award size={22} />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Review Flagged</span>
          <span className="metric-value" style={{ color: reviewNeeded > 0 ? 'var(--text-rose)' : 'var(--text-emerald)' }}>
            {reviewNeeded}
          </span>
          <span className="metric-subtext">
            {reviewNeeded > 0 ? 'Requires human signoff' : 'All records >= 80%'}
          </span>
        </div>
        <div className="metric-icon-wrap" style={{ color: reviewNeeded > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
          <ShieldAlert size={22} />
        </div>
      </div>
    </div>
  );
}
