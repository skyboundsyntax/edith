import React from 'react';
import { Database, Filter, Award, ShieldAlert } from 'lucide-react';

export default function MetricsCards({ metrics = {}, activeWorkflow = null, records = [] }) {
  const safeMetrics = metrics || {};
  const safeRecords = Array.isArray(records) ? records : [];
  const totalExtracted = safeMetrics.total_extracted ?? activeWorkflow?.total_extracted ?? safeRecords.length;
  const totalUnique = safeMetrics.total_deduplicated ?? activeWorkflow?.total_deduplicated ?? safeRecords.length;
  const duplicatesPruned = safeMetrics.duplicates_pruned ?? activeWorkflow?.duplicates_pruned ?? 0;
  const reviewNeeded = safeMetrics.human_review_count ?? activeWorkflow?.human_review_count ?? safeRecords.filter((r) => r?.human_review_required).length;
  
  // Mathematically calculated average confidence from loaded records
  const meanConfidence = safeRecords.length > 0
    ? (safeRecords.reduce((acc, r) => acc + (r?.confidence_score || 0), 0) / safeRecords.length).toFixed(1)
    : (safeMetrics.mean_confidence ? Number(safeMetrics.mean_confidence).toFixed(1) : '--');

  return (
    <div className="metrics-grid">
      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Scraped Job Postings</span>
          <span className="metric-value">{totalExtracted}</span>
          <span className="metric-subtext">From LinkedIn, Jobicy & Tech Boards</span>
        </div>
        <div className="metric-icon-wrap">
          <Database size={22} color="var(--accent-amber)" />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Unique Verified Openings</span>
          <span className="metric-value">{totalUnique}</span>
          <span className="metric-subtext" style={{ color: 'var(--text-copper)' }}>
            {duplicatesPruned} cross-platform duplicates pruned
          </span>
        </div>
        <div className="metric-icon-wrap">
          <Filter size={22} color="var(--accent-copper)" />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Jev's Job Trust Meter</span>
          <span className="metric-value">{meanConfidence !== '--' ? `${meanConfidence}%` : '--'}</span>
          <span className="metric-subtext">Source-grounded authenticity score</span>
        </div>
        <div className="metric-icon-wrap" style={{ color: 'var(--accent-emerald)' }}>
          <Award size={22} />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">Flagged / Review Required</span>
          <span className="metric-value" style={{ color: reviewNeeded > 0 ? 'var(--text-rose)' : 'var(--text-emerald)' }}>
            {reviewNeeded}
          </span>
          <span className="metric-subtext">
            {reviewNeeded > 0 ? 'Confidence < 80% or missing key terms' : '100% Passed Trust Validation'}
          </span>
        </div>
        <div className="metric-icon-wrap" style={{ color: reviewNeeded > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
          <ShieldAlert size={22} />
        </div>
      </div>
    </div>
  );
}
