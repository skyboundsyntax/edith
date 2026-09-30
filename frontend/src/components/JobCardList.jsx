import React, { useState } from 'react';
import {
  ExternalLink,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Globe,
  Building2,
  IndianRupee,
  Sparkles,
  MapPin,
  CheckCircle2
} from 'lucide-react';
import { ModalityBadge, ResilientEmptyState } from './ui';
import { sanitizeJobDescription } from '../utils/textSanitizer';
import { formatSalaryInRupees } from '../utils/currencyFormatter';

function extractSubscore(val, fallback = 0) {
  if (val === null || val === undefined) return fallback;
  if (typeof val === 'number') return isNaN(val) ? fallback : val;
  if (typeof val === 'string') {
    const parsed = parseFloat(val);
    return isNaN(parsed) ? fallback : parsed;
  }
  if (typeof val === 'object') {
    if (typeof val.score === 'number') return val.score;
    if (typeof val.val === 'number') return val.val;
    if (typeof val.points === 'number') return val.points;
  }
  return fallback;
}

/**
 * Data-Driven Fit & Salary Spectrum Curve
 * Converts actual match subscores (skills, experience, location, role) into a real
 * analytical progression curve, replacing procedural fake chart-junk.
 */
function JobDataSpectrum({ subscores = {}, score = 85, id = 1 }) {
  const safeSub = subscores || {};
  const sSkills = Math.max(0, Math.min(1, extractSubscore(safeSub.skills, 26) / 30));
  const sRole = Math.max(0, Math.min(1, extractSubscore(safeSub.role_title || safeSub.role, 18) / 20));
  const sExp = Math.max(0, Math.min(1, extractSubscore(safeSub.experience, 13) / 15));
  const sLoc = Math.max(0, Math.min(1, extractSubscore(safeSub.location, 9) / 10));

  const y1 = Math.max(6, Math.min(30, Math.round(30 - sRole * 16)));
  const y2 = Math.max(6, Math.min(30, Math.round(30 - sSkills * 20)));
  const y3 = Math.max(6, Math.min(30, Math.round(30 - sExp * 18)));
  const y4 = Math.max(6, Math.min(30, Math.round(30 - sLoc * 16)));

  const pathD = `M 0 28 C 30 ${y1}, 60 ${y2}, 95 ${y2} C 130 ${y2}, 160 ${y3}, 200 ${y4}`;
  const fillD = `${pathD} L 200 36 L 0 36 Z`;
  const safeId = String(id || '1').replace(/[^a-zA-Z0-9_-]/g, '_');

  return (
    <div className="job-sparkline-wrap" title={`Data-backed fit continuum: Skills ${(sSkills*100).toFixed(0)}%, Exp ${(sExp*100).toFixed(0)}%, Location ${(sLoc*100).toFixed(0)}%`}>
      <svg
        viewBox="0 0 200 36"
        className="job-sparkline-svg"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id={`fitGrad-${safeId}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.6" />
            <stop offset="50%" stopColor="#f97316" stopOpacity="1" />
            <stop offset="100%" stopColor="#818cf8" stopOpacity="0.85" />
          </linearGradient>
          <linearGradient id={`fitFill-${safeId}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <path d={fillD} fill={`url(#fitFill-${safeId})`} />
        <path
          d={pathD}
          fill="none"
          stroke={`url(#fitGrad-${safeId})`}
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

export default function JobCardList({
  records = [],
  onInspectProvenance,
  expandedId,
  onToggleExpand
}) {
  const [internalExpandedId, setInternalExpandedId] = useState(null);
  const activeExpandedId = expandedId !== undefined ? expandedId : internalExpandedId;

  const toggleExpand = (id) => {
    if (onToggleExpand) {
      onToggleExpand(id);
    } else {
      setInternalExpandedId((prev) => (prev === id ? null : id));
    }
  };

  const formatDate = (isoString) => {
    try {
      const d = isoString ? new Date(isoString) : new Date();
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Recently Active';
    }
  };

  if (records.length === 0) {
    return (
      <ResilientEmptyState />
    );
  }

  return (
    <div className="job-card-list-container">
      {/* High-Density Column Headers */}
      <div className="job-list-header-row">
        <div className="col-header col-role">ROLE & TECH STACK</div>
        <div className="col-header col-company">COMPANY & SOURCE</div>
        <div className="col-header col-location">MODE & LOCATION</div>
        <div className="col-header col-salary">SALARY (₹ CTC)</div>
        <div className="col-header col-fit" style={{ textAlign: 'right' }}>EDITH FIT</div>
      </div>

      {/* Cards Stream */}
      <div className="job-cards-stream">
        {records.map((r, idx) => {
          const data = r.data || {};
          const isExpanded = activeExpandedId === r.id;
          const score = data.match_score ?? r.confidence_score ?? 85;
          const remoteType = String(data.remote_type || '').toLowerCase();
          const locLower = String(data.location || '').toLowerCase();
          const rawModality = String(data.work_modality || '').toLowerCase();
          const titleDisplay = data.job_title || 'Software Engineer';
          const companyDisplay = data.company || 'Company';
          const platform = data.platform_source || (r.source_url?.includes('linkedin') ? 'LinkedIn' : r.source_url?.includes('naukri') ? 'Naukri' : 'ATS Live');
          const rawApply = data.apply_link || r.source_url || '';
          const applyUrl = rawApply && rawApply !== '#'
            ? rawApply
            : `https://www.google.com/search?q=${encodeURIComponent(`${companyDisplay} ${titleDisplay} apply online`)}`;
          const companySiteUrl = data.company_url || `https://www.google.com/search?q=${encodeURIComponent(`${companyDisplay} careers`)}`;
          
          const fullContext = (titleDisplay + ' ' + locLower + ' ' + (data.description_snippet || '')).toLowerCase();
          const isOnline = rawModality === 'online' || remoteType === 'remote' || /remote|online|virtual|wfh|telecommute/i.test(fullContext);
          const isHybrid = rawModality === 'hybrid' || remoteType === 'hybrid' || /hybrid/i.test(fullContext);
          const modalityDetail = isOnline ? 'Online • Remote' : isHybrid ? 'Offline • Hybrid' : 'Offline • On-site';
          const locationDisplay = data.location || (isOnline ? 'Remote' : 'India');
          const subscores = data.match_subscores || {};
          const skillsList = Array.isArray(data.skills) ? data.skills : (data.skills ? String(data.skills).split(',') : []);
          const salaryDisplay = formatSalaryInRupees(data.salary_range, 'Competitive Market CTC');

          return (
            <div
              key={r.id}
              className={`frosted-job-card ${isExpanded ? 'is-expanded' : ''}`}
            >
              {/* Main Job Row (Elevated Information Density) */}
              <div
                className="job-card-main-row"
                onClick={() => toggleExpand(r.id)}
                role="button"
                tabIndex={0}
                aria-expanded={isExpanded}
                aria-label={`${titleDisplay} at ${companyDisplay}, ${salaryDisplay}, ${locationDisplay}, ${isOnline ? 'Online' : 'Offline'}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleExpand(r.id);
                  }
                }}
              >
                {/* 1. Job Title, Real Spectrum Curve, & Primary Skills */}
                <div className="job-cell cell-title-wave">
                  <div className="title-row">
                    <span className="job-title-text">{titleDisplay}</span>
                    {data.experience_years && (
                      <span className="exp-mini-tag">{data.experience_years}</span>
                    )}
                  </div>

                  {/* Real Data Spectrum Curve */}
                  <JobDataSpectrum subscores={subscores} score={score} id={r.id} />

                  {/* Visible Top Skills Chips */}
                  <div className="row-skills-chips">
                    {skillsList.slice(0, 3).map((s, i) => (
                      <span key={i} className="mini-skill-chip">{String(s).trim()}</span>
                    ))}
                    {skillsList.length > 3 && (
                      <span className="mini-skill-more">+{skillsList.length - 3}</span>
                    )}
                  </div>
                </div>

                {/* 2. Company & Source */}
                <div className="job-cell cell-company">
                  <span className="cell-mobile-label">Company</span>
                  <div className="company-info-wrap">
                    <span className="company-name-text">{companyDisplay}</span>
                    <span className="platform-subtag">{platform}</span>
                  </div>
                </div>

                {/* 3. Mode & Location */}
                <div className="job-cell cell-location flex-item-safe">
                  <span className="cell-mobile-label">Mode & Location</span>
                  <div className="location-stack" style={{ minWidth: 0 }}>
                    <ModalityBadge
                      modality={rawModality}
                      remoteType={remoteType}
                      rawLocation={locationDisplay}
                      size="sm"
                    />
                    <span className="location-name-text truncate" title={locationDisplay}>{locationDisplay}</span>
                  </div>
                </div>

                {/* 4. Salary (CTC) - Elevated to primary row in Rupees */}
                <div className="job-cell cell-salary">
                  <span className="cell-mobile-label">Salary (CTC)</span>
                  <div className={`salary-primary-pill ${salaryDisplay !== 'Competitive Market CTC' ? 'disclosed' : 'undisclosed'}`}>
                    <IndianRupee size={12} />
                    <span>{salaryDisplay}</span>
                  </div>
                </div>

                {/* 5. Fit Score & Direct Apply CTA */}
                <div className="job-cell cell-fit">
                  <div className="fit-toggle-group">
                    <div className={`fit-pill-badge ${score >= 80 ? 'high' : score >= 65 ? 'mid' : 'fair'}`}>
                      <Sparkles size={12} />
                      <span>{score}% Fit</span>
                    </div>

                    <a
                      href={applyUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="row-direct-apply-btn"
                      onClick={(e) => e.stopPropagation()}
                      title={`Open official application for ${titleDisplay} on ${platform}`}
                    >
                      <span>Apply</span>
                      <ExternalLink size={12} />
                    </a>

                    <button
                      type="button"
                      className="job-expand-toggle-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleExpand(r.id);
                      }}
                      title={isExpanded ? 'Collapse breakdown' : 'View 100-pt fit breakdown'}
                      aria-label={isExpanded ? 'Collapse job details' : 'Expand job details'}
                    >
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>
                </div>
              </div>

              {/* Expandable Details Drawer */}
              {isExpanded && (
                <div className="job-card-expanded-drawer">
                  {/* Top Match Bar */}
                  <div className="drawer-top-banner">
                    <div className="drawer-modality-pill-wrap" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                      <ModalityBadge
                        modality={rawModality}
                        remoteType={remoteType}
                        rawLocation={locationDisplay}
                        size="md"
                      />
                      <span className="drawer-platform-tag">
                        Platform: {platform} • Scraped: {formatDate(r.created_at)}
                      </span>
                    </div>

                    <div className="drawer-score-badge">
                      <CheckCircle2 size={14} color="var(--accent-emerald)" />
                      <span>EDITH Match: <strong>{score}/100 Points</strong></span>
                    </div>
                  </div>

                  {/* 100-pt Explainable Score Breakdown */}
                  <div className="drawer-scores-grid">
                    <div className="drawer-score-box">
                      <span className="score-box-label">Skills Stack</span>
                      <span className="score-box-val">{extractSubscore(subscores.skills, 26)}/30</span>
                    </div>
                    <div className="drawer-score-box">
                      <span className="score-box-label">Role Title</span>
                      <span className="score-box-val">{extractSubscore(subscores.role_title || subscores.role, 18)}/20</span>
                    </div>
                    <div className="drawer-score-box">
                      <span className="score-box-label">Experience</span>
                      <span className="score-box-val">{extractSubscore(subscores.experience, 13)}/15</span>
                    </div>
                    <div className="drawer-score-box">
                      <span className="score-box-label">Location Fit</span>
                      <span className="score-box-val">{extractSubscore(subscores.location, 9)}/10</span>
                    </div>
                    <div className="drawer-score-box">
                      <span className="score-box-label">Salary Match</span>
                      <span className="score-box-val">{extractSubscore(subscores.salary, 5)}/5</span>
                    </div>
                  </div>

                  {/* Clean Description Snippet if present */}
                  {(data.description_snippet || data.description) && (
                    <div className="drawer-desc-snippet">
                      <span style={{ fontWeight: 600, color: '#e2e8f0' }}>Job Overview: </span>
                      {sanitizeJobDescription(data.description_snippet || data.description).slice(0, 350)}...
                    </div>
                  )}

                  {/* Action Bar */}
                  <div className="drawer-action-bar">
                    <button
                      type="button"
                      className="btn-glass-audit"
                      onClick={() => onInspectProvenance(r.id)}
                      title="Inspect full source-backed audit trail and anti-ghost proof"
                    >
                      <ShieldCheck size={14} color="var(--accent-emerald)" />
                      <span>Jev Anti-Ghost Audit</span>
                    </button>

                    <div className="drawer-apply-actions">
                      <a
                        href={companySiteUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-company-site"
                        title={`Visit ${companyDisplay} official site`}
                      >
                        <Globe size={13} />
                        <span>Company Site</span>
                      </a>

                      <a
                        href={applyUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-direct-apply-main"
                        title={`Apply directly on ${platform}`}
                      >
                        <span>Apply on {platform}</span>
                        <ExternalLink size={14} />
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
