import React from 'react';
import { Database, Filter, Award, ShieldAlert, TrendingUp, Sparkles } from 'lucide-react';

export default function MetricsCards({ metrics = {}, activeWorkflow = null, records = [], domain = null }) {
  const safeMetrics = metrics || {};
  const safeRecords = Array.isArray(records) ? records : [];
  const totalExtracted = safeMetrics.total_extracted ?? activeWorkflow?.total_extracted ?? safeRecords.length;
  const totalUnique = safeMetrics.total_deduplicated ?? activeWorkflow?.total_deduplicated ?? safeRecords.length;
  const duplicatesPruned = safeMetrics.duplicates_pruned ?? activeWorkflow?.duplicates_pruned ?? 0;
  const reviewNeeded = safeMetrics.human_review_count ?? activeWorkflow?.human_review_count ?? safeRecords.filter((r) => r?.human_review_required).length;
  
  // Calculate average confidence from records or fallback
  const meanConfidence = safeRecords.length > 0
    ? (safeRecords.reduce((acc, r) => acc + (r?.confidence_score || 0), 0) / safeRecords.length).toFixed(1)
    : (safeMetrics.mean_confidence ? Number(safeMetrics.mean_confidence).toFixed(1) : '--');

  const domainType = domain || activeWorkflow?.parsed_spec?.intent_parsing?.domain_type || 'TALENT_JOBS';

  let card1Label = "Scraped Job Postings";
  let card1Subtext = "From LinkedIn, Jobicy & Tech Boards";
  let card2Label = "Unique Verified Openings";
  let card2Subtext = `${duplicatesPruned} cross-platform duplicates pruned`;
  let card3Label = "Jev's Job Trust Meter";
  let card3Subtext = "Source-grounded authenticity score";
  let card4Label = "Flagged / Review Required";

  if (domainType === 'MARKET_DATA') {
    card1Label = "Ingested Market Entities";
    card1Subtext = "Seed Startups & Venture Portfolios";
    card2Label = "Unique Verified Startups";
    card2Subtext = `${duplicatesPruned} duplicates pruned & canonicalized`;
    card3Label = "Jev's Entity Trust Score";
    card3Subtext = "Source-grounded capitalization score";
    card4Label = "Flagged for Verification";
  } else if (domainType === 'SPONSORSHIPS') {
    card1Label = "Scraped Opportunities";
    card1Subtext = "Conferences, Hackathons & Tech Events";
    card2Label = "Verified Event Tiers";
    card2Subtext = `${duplicatesPruned} duplicate event packages pruned`;
    card3Label = "Partner Trust Index";
    card3Subtext = "Verified organizer lineage";
    card4Label = "Lead Review Required";
  } else if (domainType === 'GENERAL_INTELLIGENCE') {
    card1Label = "Discovered Data Records";
    card1Subtext = "Autonomous web text extraction";
    card2Label = "Unique Canonical Records";
    card2Subtext = `${duplicatesPruned} duplicate entities merged`;
    card3Label = "Data Fidelity Index";
    card3Subtext = "Deterministic schema accuracy";
    card4Label = "Flagged / Audit Needed";
  }

  return (
    <div className="metrics-grid">
      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">{card1Label}</span>
          <span className="metric-value">{totalExtracted}</span>
          <span className="metric-subtext">{card1Subtext}</span>
        </div>
        <div className="metric-icon-wrap">
          <Database size={22} color="var(--accent-amber)" />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">{card2Label}</span>
          <span className="metric-value">{totalUnique}</span>
          <span className="metric-subtext" style={{ color: 'var(--text-copper)' }}>
            {card2Subtext}
          </span>
        </div>
        <div className="metric-icon-wrap">
          <Filter size={22} color="var(--accent-copper)" />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">{card3Label}</span>
          <span className="metric-value">{meanConfidence !== '--' ? `${meanConfidence}%` : '--'}</span>
          <span className="metric-subtext">{card3Subtext}</span>
        </div>
        <div className="metric-icon-wrap" style={{ color: 'var(--accent-emerald)' }}>
          <Award size={22} />
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-info">
          <span className="metric-label">{card4Label}</span>
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
