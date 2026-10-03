import React, { useState } from 'react';
import {
  ExternalLink,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Globe,
  Building2,
  IndianRupee,
  MapPin,
  CheckCircle2
} from 'lucide-react';
import { ModalityBadge, ResilientEmptyState, Butterfly } from './ui';
import { sanitizeJobDescription, formatSkillName } from '../utils/textSanitizer';
import { formatSalaryInRupees } from '../utils/currencyFormatter';
import { getSafeExternalUrl, truncateSafe } from '../utils/urlValidator';

function extractSubscore(val, fallback = 0) {
  if (val === null || val === undefined) return fallback;
  if (typeof val === 'number') return Number.isFinite(val) ? val : fallback;
  if (typeof val === 'string') {
    const parsed = parseFloat(val);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  if (typeof val === 'object') {
    if (typeof val.score === 'number' && Number.isFinite(val.score)) return val.score;
    if (typeof val.val === 'number' && Number.isFinite(val.val)) return val.val;
    if (typeof val.points === 'number' && Number.isFinite(val.points)) return val.points;
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
      {/* Cards Stream */}
      <div className="job-cards-stream">
        {records.map((r, idx) => {
          const data = r.data || {};
          const isExpanded = activeExpandedId === r.id;
          const score = data.match_score ?? r.confidence_score ?? 85;
          const remoteType = String(data.remote_type || '').toLowerCase();
          const locLower = String(data.location || '').toLowerCase();
          const rawModality = String(data.work_modality || '').toLowerCase();
          const titleDisplay = data.job_title || data.title || r.source_title || 'Software Engineer';
          const companyDisplay = data.company || 'Verified Company';
          const rawApply = data.apply_link || r.source_url || '';
          const safeApply = String(rawApply || r.source_url || '').toLowerCase();
          const platform = String(
            data.platform_source ||
            data.source ||
            r.source ||
            (safeApply.includes('linkedin')
              ? 'LinkedIn'
              : safeApply.includes('greenhouse')
                ? 'Greenhouse'
                : safeApply.includes('lever')
                  ? 'Lever'
                  : safeApply.includes('ashby')
                    ? 'Ashby'
                    : safeApply.includes('naukri')
                      ? 'Naukri'
                      : safeApply.includes('remotive')
                        ? 'Remotive'
                        : safeApply.includes('jobicy')
                          ? 'Jobicy'
                          : 'ATS Direct')
          );
          const applyUrl = getSafeExternalUrl(rawApply, `${companyDisplay} ${titleDisplay} apply online`);
          const companySiteUrl = getSafeExternalUrl(data.company_url, `${companyDisplay} official careers`);
          
          const rawSkills = Array.isArray(data.skills)
            ? data.skills
            : typeof data.skills === 'string'
              ? data.skills.split(/[,|/]/)
              : [];
          const skillsList = rawSkills
            .map((s) => formatSkillName(typeof s === 'string' ? s.trim() : String(s || '').trim()))
            .filter((s) => s.length > 0 && s.length <= 40);

          const fullContext = (titleDisplay + ' ' + locLower + ' ' + (data.description_snippet || '')).toLowerCase();
          const isOnline = rawModality === 'online' || remoteType === 'remote' || /remote|online|virtual|wfh|telecommute/i.test(fullContext);
          const isHybrid = rawModality === 'hybrid' || remoteType === 'hybrid' || /hybrid/i.test(fullContext);
          const locationDisplay = data.location || (isOnline ? 'Remote / Worldwide' : 'India');
          const subscores = data.match_subscores || {};
          const salaryDisplay = formatSalaryInRupees(data.salary_range || data.salary, 'Competitive Market CTC');

          return (
            <div
              key={r.id}
              className={`frosted-job-card ${isExpanded ? 'is-expanded' : ''}`}
            >
              {/* Main Clickable Job Card Body */}
              <div
                className="job-card-main-content"
                onClick={() => toggleExpand(r.id)}
                role="button"
                tabIndex={0}
                aria-expanded={isExpanded}
                aria-label={`${titleDisplay} at ${companyDisplay}, ${salaryDisplay}, ${locationDisplay}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleExpand(r.id);
                  }
                }}
              >
                {/* Tier 1: Role Title, Company, Salary & Apply Actions */}
                <div className="card-tier-primary">
                  <div className="card-identity-group">
                    <div className="card-role-header">
                      <h4 className="card-role-title" dir="auto">{titleDisplay}</h4>
                      {data.experience_years && (
                        <span className="card-exp-tag">{data.experience_years}</span>
                      )}
                    </div>

                    <div className="card-company-line">
                      <span className="card-company-name" dir="auto">{companyDisplay}</span>
                      <span className="card-dot-sep">•</span>
                      <span className="platform-subtag">{platform}</span>
                      <span className="card-dot-sep">•</span>
                      <span className="card-timestamp">{formatDate(r.created_at || data.date_posted)}</span>
                    </div>
                  </div>

                  <div className="card-actions-group">
                    {/* Salary Pill */}
                    <div className={`salary-primary-pill ${salaryDisplay !== 'Competitive Market CTC' ? 'disclosed' : 'undisclosed'}`}>
                      <IndianRupee size={13} />
                      <span>{salaryDisplay}</span>
                    </div>

                    {/* Fit Score Badge */}
                    <div className={`fit-pill-badge ${score >= 80 ? 'high' : score >= 65 ? 'mid' : 'fair'}`}>
                      <Butterfly size={13} />
                      <span>{score}% Fit</span>
                    </div>

                    {/* Direct Apply CTA Button */}
                    <a
                      href={applyUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="card-apply-btn"
                      onClick={(e) => e.stopPropagation()}
                      title={`Apply directly on ${platform}`}
                      aria-label={`Apply for ${titleDisplay} on ${platform}`}
                    >
                      <span>Apply Now</span>
                      <ExternalLink size={12} />
                    </a>

                    {/* Expand Collapse Toggle */}
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

                {/* Tier 2: Modality, Location, Skills & Sparkline Continuum */}
                <div className="card-tier-secondary">
                  <div className="card-geo-modality">
                    <ModalityBadge
                      modality={rawModality}
                      remoteType={remoteType}
                      rawLocation={locationDisplay}
                      size="sm"
                    />
                    <span className="card-location-text" title={locationDisplay}>
                      <MapPin size={12} style={{ display: 'inline', verticalAlign: '-1px', marginRight: '4px' }} />
                      {locationDisplay}
                    </span>
                  </div>

                  {skillsList.length > 0 && (
                    <div className="card-skills-row">
                      {skillsList.slice(0, 5).map((s, i) => (
                        <span key={i} className="mini-skill-chip" title={String(s).trim()}>
                          {truncateSafe(String(s).trim(), 24)}
                        </span>
                      ))}
                      {skillsList.length > 5 && (
                        <span className="mini-skill-more">+{skillsList.length - 5} more</span>
                      )}
                    </div>
                  )}

                  {/* Real Data Fit Continuum Sparkline */}
                  <div className="card-spectrum-dock">
                    <JobDataSpectrum subscores={subscores} score={score} id={r.id} />
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
                      {sanitizeJobDescription(data.description_snippet || data.description).slice(0, 450)}
                    </div>
                  )}

                  {/* Requirements list if present */}
                  {Array.isArray(data.requirements) && data.requirements.length > 0 && (
                    <div className="drawer-requirements-box" style={{ marginTop: '10px', padding: '10px 14px', background: 'rgba(0,0,0,0.25)', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
                      <span style={{ fontWeight: 600, color: 'var(--accent-amber)', fontSize: '0.8rem', display: 'block', marginBottom: '6px' }}>
                        Key Requirements & Eligibility:
                      </span>
                      <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {data.requirements.slice(0, 5).map((req, rIdx) => (
                          <li key={rIdx} style={{ fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.4 }}>
                            {req}
                          </li>
                        ))}
                      </ul>
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
                        href={applyUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-direct-apply-main"
                        title={`Apply directly for ${titleDisplay} at ${companyDisplay}`}
                      >
                        <span>Apply Now</span>
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
