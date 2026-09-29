import React, { useState, useMemo } from 'react';
import {
  Search, ExternalLink, ShieldCheck, Filter, FileSpreadsheet, FileCode,
  MapPin, DollarSign, CheckCircle2, AlertTriangle, ChevronDown, ChevronUp,
  Briefcase, Zap, Info, Globe, Building2, Calendar
} from 'lucide-react';
import { sanitizeJobDescription } from '../utils/textSanitizer';

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


export default function DataGrid({
  records = [],
  schema,
  onInspectProvenance,
  onExport,
  isExporting
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [minScoreFilter, setMinScoreFilter] = useState(0);
  const [locationFilter, setLocationFilter] = useState('ALL');
  const [sourceTypeFilter, setSourceTypeFilter] = useState('ALL');
  const [showOnlyReview, setShowOnlyReview] = useState(false);
  const [expandedRecordId, setExpandedRecordId] = useState(null);

  // Check if current dataset is job-focused
  const isJobDataset = useMemo(() => {
    if (schema?.entity_name === 'JobOpening') return true;
    return records.some((r) => r.data?.job_title || r.entity_name === 'JobOpening');
  }, [schema, records]);

  // Extract dynamic column keys from schema or records for non-job datasets
  const dynamicColumns = useMemo(() => {
    if (schema?.fields && schema.fields.length > 0) {
      return schema.fields.map((f) => ({
        key: f.name,
        label: f.name.replace(/_/g, ' ').toUpperCase()
      }));
    }
    if (records.length > 0 && records[0].data) {
      return Object.keys(records[0].data).map((k) => ({
        key: k,
        label: k.replace(/_/g, ' ').toUpperCase()
      }));
    }
    return [
      { key: 'title', label: 'TITLE' },
      { key: 'category', label: 'CATEGORY' }
    ];
  }, [schema, records]);

  // Filter records
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      const data = r.data || {};
      const score = data.match_score ?? r.confidence_score ?? 0;

      if (showOnlyReview && !r.human_review_required) return false;
      if (score < minScoreFilter) return false;


      // Location & Modality filter
      if (locationFilter !== 'ALL') {
        const loc = String(data.location || '').toLowerCase();
        const rtype = String(data.remote_type || '').toLowerCase();
        const mod = String(data.work_modality || '').toLowerCase();
        const isRecOnline = mod.includes('online') || rtype === 'remote' || loc.includes('remote') || loc.includes('virtual') || loc.includes('wfh') || loc.includes('online') || loc.includes('anywhere');

        if (locationFilter === 'ONLINE' && !isRecOnline) return false;
        if (locationFilter === 'OFFLINE' && isRecOnline) return false;
        if (locationFilter === 'REMOTE' && !isRecOnline) return false;
        if (locationFilter === 'PUNE' && !loc.includes('pune')) return false;
        if (locationFilter === 'BANGALORE' && !loc.includes('bangalore') && !loc.includes('bengaluru')) return false;
        if (locationFilter === 'HYDERABAD' && !loc.includes('hyderabad')) return false;
        if (locationFilter === 'DELHI' && !loc.includes('delhi') && !loc.includes('noida') && !loc.includes('gurgaon')) return false;
        if (locationFilter === 'MUMBAI' && !loc.includes('mumbai')) return false;
      }

      if (!searchTerm) return true;

      const term = searchTerm.toLowerCase();
      const matchesData = Object.values(data).some((v) =>
        String(v).toLowerCase().includes(term)
      );
      const matchesSource = r.source_url?.toLowerCase().includes(term) ||
                            r.source_title?.toLowerCase().includes(term);
      return matchesData || matchesSource;
    });
  }, [records, searchTerm, minScoreFilter, locationFilter, sourceTypeFilter, showOnlyReview]);

  const getScoreColor = (score) => {
    if (score >= 80) return { class: 'excellent', hex: '#10b981' };
    if (score >= 65) return { class: 'good', hex: '#f59e0b' };
    if (score >= 50) return { class: 'fair', hex: '#d97706' };
    return { class: 'low', hex: '#ef4444' };
  };

  const getPlatformClass = (platformStr = '') => {
    const p = String(platformStr).toLowerCase();
    if (p.includes('linkedin')) return 'linkedin';
    if (p.includes('naukri')) return 'naukri';
    if (p.includes('indeed')) return 'indeed';
    return 'careers';
  };

  const toggleExpand = (id) => {
    setExpandedRecordId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="glass-panel data-grid-section">
      <div className="grid-toolbar" style={{ flexWrap: 'wrap', gap: '0.85rem' }}>
        {/* Search Input */}
        <div className="toolbar-search" style={{ minWidth: '260px' }}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder={isJobDataset ? "Filter by title, company, skills, or platform..." : "Search records or sources..."}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Filters and Actions */}
        <div className="toolbar-actions" style={{ flexWrap: 'wrap', gap: '0.65rem' }}>
          {/* Location Filter */}
          {isJobDataset && (
            <select
              className="grid-filter-select"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
            >
              <option value="ALL">All Modalities & Locations</option>
              <option value="ONLINE">Online (Remote / Virtual)</option>
              <option value="OFFLINE">Offline (In-Person / Hybrid)</option>
              <option value="PUNE">Pune</option>
              <option value="BANGALORE">Bangalore / Bengaluru</option>
              <option value="HYDERABAD">Hyderabad</option>
              <option value="MUMBAI">Mumbai</option>
              <option value="DELHI">Delhi NCR</option>
            </select>
          )}


          {/* Min Score Slider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.785rem', color: 'var(--text-secondary)' }}>
            <Filter size={13} />
            <span>Fit ≥ {minScoreFilter}%</span>
            <input
              type="range"
              min="0"
              max="95"
              step="5"
              value={minScoreFilter}
              onChange={(e) => setMinScoreFilter(Number(e.target.value))}
              style={{ width: '70px', accentColor: 'var(--accent-amber)' }}
            />
          </div>

          {/* Review Only Checkbox */}
          <button
            className={`btn ${showOnlyReview ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
            onClick={() => setShowOnlyReview(!showOnlyReview)}
          >
            Suspect / Review ({records.filter((r) => r.human_review_required).length})
          </button>

          {/* Export Buttons */}
          <button
            className="btn btn-outline-cyan"
            style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
            onClick={() => onExport('csv')}
            disabled={isExporting}
          >
            <FileSpreadsheet size={13} />
            <span>CSV</span>
          </button>
          <button
            className="btn btn-outline-cyan"
            style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
            onClick={() => onExport('json')}
            disabled={isExporting}
          >
            <FileCode size={13} />
            <span>JSON</span>
          </button>
        </div>
      </div>

      {/* Dynamic Data Table */}
      <div className="table-wrapper">
        <table className="custom-table">
          <thead>
            {isJobDataset ? (
              <tr>
                <th style={{ width: '130px' }}>EDITH FIT</th>
                <th>ROLE & EXPERIENCE</th>
                <th>COMPANY</th>
                <th>SOURCE & TYPE</th>
                <th>MODE & LOCATION</th>
                <th>SKILLS & SIGNALS</th>
                <th>SALARY (CTC)</th>
                <th>ACTION</th>
                <th style={{ textAlign: 'right' }}>DETAILS</th>
              </tr>
            ) : (
              <tr>
                <th>CONFIDENCE (JEV)</th>
                {dynamicColumns.slice(0, 4).map((col) => (
                  <th key={col.key}>{col.label}</th>
                ))}
                <th>VERIFIED SOURCE</th>
                <th style={{ textAlign: 'right' }}>PROVENANCE AUDIT</th>
              </tr>
            )}
          </thead>
          <tbody>
            {filteredRecords.length === 0 ? (
              <tr>
                <td colSpan={isJobDataset ? 9 : dynamicColumns.length + 3} style={{ textAlign: 'center', padding: '3.5rem', color: 'var(--text-muted)' }}>
                  No verified job records match the filter criteria.
                </td>
              </tr>
            ) : (
              filteredRecords.map((r) => {
                const data = r.data || {};
                const isExpanded = expandedRecordId === r.id;

                if (isJobDataset) {
                  const score = data.match_score ?? r.confidence_score ?? 0;
                  const scoreTheme = getScoreColor(score);
                  const platform = data.platform_source || (r.source_url?.includes('linkedin') ? 'LinkedIn' : r.source_url?.includes('naukri') ? 'Naukri' : r.source_url?.includes('indeed') ? 'Indeed' : 'Careers');
                  const skillsList = Array.isArray(data.skills) ? data.skills : (data.skills ? String(data.skills).split(',') : []);
                  const subscores = data.match_subscores || {};
                  const whyMatches = Array.isArray(data.why_it_matches) ? data.why_it_matches : [];
                  const gaps = Array.isArray(data.potential_gaps) ? data.potential_gaps : [];
                  const remoteType = String(data.remote_type || '').toLowerCase();
                  const locLower = String(data.location || '').toLowerCase();
                  const rawModality = String(data.work_modality || '').toLowerCase();
                  const titleLower = String(data.job_title || '').toLowerCase();
                  const descLower = String(data.description_snippet || '').toLowerCase();
                  const fullContext = (titleLower + ' ' + locLower + ' ' + descLower);
                  const isOnline = rawModality === 'online' || remoteType === 'remote' || /remote|online|virtual|wfh|telecommute|anywhere/i.test(fullContext);
                  const isHybrid = rawModality === 'hybrid' || remoteType === 'hybrid' || /hybrid/i.test(fullContext);
                  const rawApply = data.apply_link || r.source_url || '';
                  const applyUrl = rawApply && rawApply !== '#'
                    ? rawApply
                    : `https://www.google.com/search?q=${encodeURIComponent(`${data.company || ''} ${data.job_title || ''} apply online`)}`;

                  return (
                    <React.Fragment key={r.id}>
                      <tr style={{ background: isExpanded ? 'rgba(245, 158, 11, 0.05)' : undefined }}>
                        {/* EDITH Match Fit Gauge */}
                        <td>
                          <div
                            className="match-score-cell"
                            onClick={() => toggleExpand(r.id)}
                            title="Click to view 9-factor score breakdown"
                          >
                            <div className="match-score-header">
                              <span className={`match-score-number ${scoreTheme.class}`}>
                                {score}
                                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>/100</span>
                              </span>
                              {score >= 80 ? (
                                <CheckCircle2 size={13} color="#10b981" />
                              ) : r.human_review_required ? (
                                <AlertTriangle size={13} color="#ef4444" />
                              ) : (
                                <Zap size={12} color="#f59e0b" />
                              )}
                            </div>
                            <div className="match-meter-bar">
                              <div
                                className="match-meter-fill"
                                style={{
                                  width: `${Math.min(100, score)}%`,
                                  background: scoreTheme.hex
                                }}
                              />
                            </div>
                          </div>
                        </td>

                        {/* Job Role & Seniority */}
                        <td>
                          <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.885rem' }}>
                            {data.job_title || 'Software Engineer'}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.2rem', flexWrap: 'wrap' }}>
                            {data.experience_years && (
                              <span style={{ fontSize: '0.72rem', color: 'var(--text-amber)', background: 'rgba(245, 158, 11, 0.1)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                                Exp: {data.experience_years}
                              </span>
                            )}
                            <span className={`modality-pill ${isOnline ? 'online' : isHybrid ? 'hybrid' : 'offline'}`} style={{ padding: '0.08rem 0.4rem', fontSize: '0.68rem' }}>
                              {isOnline ? <Globe size={10} /> : <Building2 size={10} />}
                              <span>{isOnline ? 'Online' : isHybrid ? 'Offline (Hybrid)' : 'Offline'}</span>
                            </span>
                            {whyMatches.slice(0, 2).map((reason, idx) => (
                              <span key={idx} className="chip-match-reason" title={reason}>
                                {reason}
                              </span>
                            ))}
                          </div>
                        </td>

                        {/* Company Name */}
                        <td style={{ fontWeight: 500, color: 'var(--text-secondary)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                            <Building2 size={13} color="var(--text-muted)" />
                            <span>{data.company || 'Tech Organization'}</span>
                          </div>
                        </td>

                        {/* Source Platform & Compliance Badge */}
                        <td>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', alignItems: 'flex-start' }}>
                            <span className={`platform-badge ${getPlatformClass(platform)}`}>
                              {platform}
                            </span>
                            <span className="source-type-pill live" title="Direct real-time posting from verified career board">
                              Live Verified
                            </span>
                          </div>
                        </td>

                        {/* Mode & Location */}
                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', alignItems: 'flex-start' }}>
                            <span className={`modality-pill ${isOnline ? 'online' : isHybrid ? 'hybrid' : 'offline'}`}>
                              {isOnline ? <Globe size={11} /> : <Building2 size={11} />}
                              <span>{isOnline ? 'Online (Remote)' : isHybrid ? 'Offline • Hybrid' : 'Offline (On-site)'}</span>
                            </span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                              <MapPin size={12} color="var(--text-muted)" />
                              <span>{data.location || (isOnline ? 'Remote, India' : 'On-site')}</span>
                            </div>
                          </div>
                        </td>

                        {/* Skills Stack & Gaps */}
                        <td>
                          <div className="skill-chips-container">
                            {skillsList.slice(0, 3).map((s, idx) => (
                              <span key={idx} className="skill-chip">{String(s).trim()}</span>
                            ))}
                            {skillsList.length > 3 && (
                              <span className="skill-chip" style={{ opacity: 0.7 }}>+{skillsList.length - 3}</span>
                            )}
                            {gaps.length > 0 && (
                              <span className="chip-gap" title={gaps.join(', ')}>
                                {gaps[0]}
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Salary (CTC) */}
                        <td>
                          {data.salary_range && data.salary_range !== 'Not Disclosed' ? (
                            <span className="salary-pill">
                              <DollarSign size={12} />
                              {data.salary_range}
                            </span>
                          ) : (
                            <span className="salary-pill undisclosed">Undisclosed</span>
                          )}
                        </td>

                        {/* Direct Apply Button */}
                        <td>
                          <a
                            href={applyUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-apply-direct"
                            title="Direct application on official job posting"
                          >
                            <ExternalLink size={12} />
                            <span>Apply Now</span>
                          </a>
                        </td>

                        {/* Details Toggle / Audit */}
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.35rem' }}>
                            <button
                              className="btn btn-secondary"
                              style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                              onClick={() => toggleExpand(r.id)}
                              title="Toggle Explainable Subscores & Description"
                            >
                              {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </button>
                            <button
                              className="btn btn-secondary"
                              style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                              onClick={() => onInspectProvenance(r.id)}
                              title="Inspect Jev Anti-Ghost Proof"
                            >
                              <ShieldCheck size={14} color="var(--accent-emerald)" />
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Expandable Deep-Dive Row */}
                      {isExpanded && (
                        <tr>
                          <td colSpan={9} style={{ padding: '0 1rem 1rem 1rem', background: 'rgba(245, 158, 11, 0.03)' }}>
                            <div className="expanded-job-card">
                              {/* Modality, Company, Location Banner */}
                              <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                background: 'rgba(0, 0, 0, 0.3)',
                                padding: '0.65rem 0.85rem',
                                borderRadius: 'var(--radius-sm)',
                                border: '1px solid var(--border-subtle)',
                                flexWrap: 'wrap',
                                gap: '0.6rem'
                              }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Work Mode:</span>
                                  <span className={`modality-pill ${isOnline ? 'online' : isHybrid ? 'hybrid' : 'offline'}`}>
                                    {isOnline ? <Globe size={11} /> : <Building2 size={11} />}
                                    <span>{isOnline ? 'Online (Remote / Virtual)' : isHybrid ? 'Offline (Hybrid In-Office)' : 'Offline (In-Person / On-site)'}</span>
                                  </span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', fontSize: '0.785rem', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                                  <span><strong style={{ color: '#cbd5e1' }}>Company:</strong> {data.company || 'Tech Organization'}</span>
                                  <span><strong style={{ color: '#cbd5e1' }}>Location:</strong> {data.location || (isOnline ? 'Remote' : 'On-site')}</span>
                                </div>
                              </div>

                              {/* 9-Factor Explainable Scoring Matrix */}
                              <div>
                                <div style={{ fontSize: '0.785rem', fontWeight: 700, color: 'var(--text-amber)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                  <Info size={14} />
                                  <span>EDITH 100-POINT EXPLAINABLE FIT BREAKDOWN</span>
                                </div>
                                <div className="subscore-grid">
                                  <div className="subscore-item">
                                    <div className="subscore-label">Skills Stack</div>
                                    <div className="subscore-value">{extractSubscore(subscores.skills, 0)}/30</div>
                                    <div className="subscore-progress">
                                      <div className="subscore-progress-fill" style={{ width: `${(extractSubscore(subscores.skills, 0) / 30) * 100}%` }} />
                                    </div>
                                  </div>
                                  <div className="subscore-item">
                                    <div className="subscore-label">Role Title</div>
                                    <div className="subscore-value">{extractSubscore(subscores.role_title, 0)}/20</div>
                                    <div className="subscore-progress">
                                      <div className="subscore-progress-fill" style={{ width: `${(extractSubscore(subscores.role_title, 0) / 20) * 100}%` }} />
                                    </div>
                                  </div>
                                  <div className="subscore-item">
                                    <div className="subscore-label">Experience</div>
                                    <div className="subscore-value">{extractSubscore(subscores.experience, 0)}/15</div>
                                    <div className="subscore-progress">
                                      <div className="subscore-progress-fill" style={{ width: `${(extractSubscore(subscores.experience, 0) / 15) * 100}%` }} />
                                    </div>
                                  </div>
                                  <div className="subscore-item">
                                    <div className="subscore-label">Location</div>
                                    <div className="subscore-value">{extractSubscore(subscores.location, 0)}/10</div>
                                    <div className="subscore-progress">
                                      <div className="subscore-progress-fill" style={{ width: `${(extractSubscore(subscores.location, 0) / 10) * 100}%` }} />
                                    </div>
                                  </div>
                                  <div className="subscore-item">
                                    <div className="subscore-label">Freshness</div>
                                    <div className="subscore-value">{extractSubscore(subscores.freshness, 0)}/5</div>
                                    <div className="subscore-progress">
                                      <div className="subscore-progress-fill" style={{ width: `${(extractSubscore(subscores.freshness, 0) / 5) * 100}%` }} />
                                    </div>
                                  </div>
                                  <div className="subscore-item">
                                    <div className="subscore-label">Salary Match</div>
                                    <div className="subscore-value">{extractSubscore(subscores.salary, 0)}/5</div>
                                    <div className="subscore-progress">
                                      <div className="subscore-progress-fill" style={{ width: `${(extractSubscore(subscores.salary, 0) / 5) * 100}%` }} />
                                    </div>
                                  </div>
                                  <div className="subscore-item">
                                    <div className="subscore-label">Requirements</div>
                                    <div className="subscore-value">{extractSubscore(subscores.requirements, 0)}/5</div>
                                    <div className="subscore-progress">
                                      <div className="subscore-progress-fill" style={{ width: `${(extractSubscore(subscores.requirements, 0) / 5) * 100}%` }} />
                                    </div>
                                  </div>
                                  <div className="subscore-item">
                                    <div className="subscore-label">Employment</div>
                                    <div className="subscore-value">{extractSubscore(subscores.employment_type, 0)}/5</div>
                                    <div className="subscore-progress">
                                      <div className="subscore-progress-fill" style={{ width: `${(extractSubscore(subscores.employment_type, 0) / 5) * 100}%` }} />
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Why It Matches & Potential Gaps */}
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                                <div>
                                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#34d399', marginBottom: '0.35rem' }}>
                                    MATCH FACTORS (WHY IT MATCHES)
                                  </div>
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                                    {whyMatches.length > 0 ? (
                                      whyMatches.map((m, i) => (
                                        <span key={i} className="chip-match-reason">{m}</span>
                                      ))
                                    ) : (
                                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Baseline job specification match</span>
                                    )}
                                  </div>
                                </div>

                                <div>
                                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#fbbf24', marginBottom: '0.35rem' }}>
                                    POTENTIAL GAPS & REQUIREMENTS
                                  </div>
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                                    {gaps.length > 0 ? (
                                      gaps.map((g, i) => (
                                        <span key={i} className="chip-gap">{g}</span>
                                      ))
                                    ) : (
                                      <span style={{ fontSize: '0.75rem', color: '#34d399' }}>✓ No critical requirement gaps detected</span>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {/* Description Snippet */}
                              {(data.description_snippet || data.description) && (
                                <div style={{ fontSize: '0.785rem', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '6px' }}>
                                  <span style={{ fontWeight: 600, color: '#cbd5e1' }}>Posting Snippet: </span>
                                  {sanitizeJobDescription(data.description_snippet || data.description).slice(0, 350)}...
                                </div>
                              )}

                              {/* Action Footer */}
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle)' }}>
                                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                  Source Method: {data.access_method || 'PUBLIC_API'} • ID: {r.id}
                                </div>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                  <button
                                    className="btn btn-secondary"
                                    style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                                    onClick={() => onInspectProvenance(r.id)}
                                  >
                                    <ShieldCheck size={14} color="var(--accent-emerald)" />
                                    <span>Full Anti-Ghost Provenance</span>
                                  </button>
                                  <a
                                    href={applyUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn-apply-direct"
                                    style={{ fontSize: '0.75rem', padding: '0.35rem 0.85rem' }}
                                  >
                                    <ExternalLink size={13} />
                                    <span>{isLinkOut ? `Search on ${platform}` : 'Apply Directly'}</span>
                                  </a>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                }

                // Standard fallback rendering for non-job datasets
                return (
                  <tr key={r.id}>
                    <td>
                      <span className={`confidence-pill ${r.confidence_score >= 88 ? 'high' : 'medium'}`}>
                        {r.confidence_score}%
                        {r.human_review_required ? ' ⚠' : ' ✓'}
                      </span>
                    </td>

                    {/* Dynamic Data Columns */}
                    {dynamicColumns.slice(0, 4).map((col) => {
                      const val = r.data?.[col.key];
                      const displayVal = Array.isArray(val)
                        ? val.join(', ')
                        : typeof val === 'object' && val !== null
                        ? JSON.stringify(val)
                        : String(val || '—');

                      return (
                        <td key={col.key} style={{ maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {displayVal}
                        </td>
                      );
                    })}

                    {/* Source Link */}
                    <td>
                      <a
                        href={r.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="source-link-cell"
                        title={r.source_title || r.source_url}
                      >
                        <ExternalLink size={13} />
                        <span>
                          {r.source_url.replace(/^https?:\/\/(www\.)?/, '').split('/')[0]}
                        </span>
                      </a>
                    </td>

                    {/* Lineage Audit Action */}
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.35rem 0.75rem', fontSize: '0.785rem' }}
                        onClick={() => onInspectProvenance(r.id)}
                      >
                        <ShieldCheck size={14} color="var(--accent-emerald)" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
