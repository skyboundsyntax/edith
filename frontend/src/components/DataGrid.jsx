import React, { useState, useMemo } from 'react';
import { Search, ExternalLink, ShieldCheck, Filter, FileSpreadsheet, FileCode, Briefcase, MapPin, DollarSign, CheckCircle2, AlertTriangle, Send } from 'lucide-react';

export default function DataGrid({
  records = [],
  schema,
  onInspectProvenance,
  onExport,
  isExporting
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [minConfidenceFilter, setMinConfidenceFilter] = useState(0);
  const [showOnlyReview, setShowOnlyReview] = useState(false);

  // Check if current dataset is job-focused
  const isJobDataset = useMemo(() => {
    if (schema?.entity_name === 'JobOpening') return true;
    return records.some((r) => r.data?.job_title || r.entity_name === 'JobOpening');
  }, [schema, records]);

  // Extract dynamic column keys from schema or records
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
      if (showOnlyReview && !r.human_review_required) return false;
      if (r.confidence_score < minConfidenceFilter) return false;
      if (!searchTerm) return true;

      const term = searchTerm.toLowerCase();
      // Search in data values
      const matchesData = Object.values(r.data || {}).some((v) =>
        String(v).toLowerCase().includes(term)
      );
      const matchesSource = r.source_url?.toLowerCase().includes(term) ||
                            r.source_title?.toLowerCase().includes(term);
      return matchesData || matchesSource;
    });
  }, [records, searchTerm, minConfidenceFilter, showOnlyReview]);

  const getConfidenceClass = (score, reviewRequired) => {
    if (reviewRequired || score < 80) return 'review';
    if (score >= 88) return 'high';
    return 'medium';
  };

  const getPlatformClass = (platformStr = '') => {
    const p = String(platformStr).toLowerCase();
    if (p.includes('linkedin')) return 'linkedin';
    if (p.includes('naukri')) return 'naukri';
    if (p.includes('indeed')) return 'indeed';
    return 'careers';
  };

  return (
    <div className="glass-panel data-grid-section">
      <div className="grid-toolbar">
        {/* Search Input */}
        <div className="toolbar-search">
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder={isJobDataset ? "Filter by role, skills, company, or platform..." : "Search records, entities, or sources..."}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Filters and Actions */}
        <div className="toolbar-actions">
          {/* Min Confidence Slider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <Filter size={14} />
            <span>Jev Trust Meter ≥ {minConfidenceFilter}%</span>
            <input
              type="range"
              min="0"
              max="95"
              step="5"
              value={minConfidenceFilter}
              onChange={(e) => setMinConfidenceFilter(Number(e.target.value))}
              style={{ width: '80px', accentColor: 'var(--accent-cyan)' }}
            />
          </div>

          {/* Review Only Checkbox */}
          <button
            className={`btn ${showOnlyReview ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.785rem', padding: '0.4rem 0.75rem' }}
            onClick={() => setShowOnlyReview(!showOnlyReview)}
          >
            Suspect / Review ({records.filter((r) => r.human_review_required).length})
          </button>

          {/* Export Buttons */}
          <button
            className="btn btn-outline-cyan"
            style={{ fontSize: '0.785rem', padding: '0.4rem 0.75rem' }}
            onClick={() => onExport('csv')}
            disabled={isExporting}
          >
            <FileSpreadsheet size={14} />
            <span>CSV</span>
          </button>
          <button
            className="btn btn-outline-cyan"
            style={{ fontSize: '0.785rem', padding: '0.4rem 0.75rem' }}
            onClick={() => onExport('json')}
            disabled={isExporting}
          >
            <FileCode size={14} />
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
                <th style={{ width: '170px' }}>JEV'S TRUST METER</th>
                <th>ROLE & EXPERIENCE</th>
                <th>COMPANY</th>
                <th>PLATFORM</th>
                <th>LOCATION</th>
                <th>KEY SKILLS</th>
                <th>SALARY (CTC)</th>
                <th>ACTION</th>
                <th style={{ textAlign: 'right' }}>TRUST AUDIT</th>
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
                const confClass = getConfidenceClass(r.confidence_score, r.human_review_required);
                const isHighTrust = r.confidence_score >= 88 && !r.human_review_required;
                const data = r.data || {};

                if (isJobDataset) {
                  const platform = data.platform_source || (r.source_url?.includes('linkedin') ? 'LinkedIn' : r.source_url?.includes('naukri') ? 'Naukri' : r.source_url?.includes('indeed') ? 'Indeed' : 'Careers');
                  const applyUrl = data.apply_link || r.source_url;
                  const skillsList = Array.isArray(data.skills) ? data.skills : (data.skills ? String(data.skills).split(',') : []);

                  return (
                    <tr key={r.id}>
                      {/* Jev Trust Meter Gauge */}
                      <td>
                        <div className={`trust-meter-badge ${confClass}`} title={`Jev Trust Score: ${r.confidence_score}% - ${isHighTrust ? 'Verified Authentic' : 'Flagged for Verification'}`}>
                          {isHighTrust ? <CheckCircle2 size={13} color="#34d399" /> : <AlertTriangle size={13} color="#f87171" />}
                          <span>{r.confidence_score}%</span>
                          <div className="trust-meter-gauge-bar">
                            <div
                              className="trust-meter-gauge-fill"
                              style={{
                                width: `${Math.min(100, r.confidence_score)}%`,
                                background: isHighTrust ? '#10b981' : confClass === 'medium' ? '#0ea5e9' : '#ef4444'
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
                        {data.experience_years && (
                          <div style={{ fontSize: '0.735rem', color: 'var(--text-cyan)', marginTop: '0.15rem' }}>
                            Exp: {data.experience_years}
                          </div>
                        )}
                      </td>

                      {/* Company Name */}
                      <td style={{ fontWeight: 500, color: 'var(--text-secondary)' }}>
                        {data.company || 'Tech Organization'}
                      </td>

                      {/* Platform Source Badge */}
                      <td>
                        <span className={`platform-badge ${getPlatformClass(platform)}`}>
                          {platform}
                        </span>
                      </td>

                      {/* Location */}
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          <MapPin size={12} color="var(--text-muted)" />
                          <span>{data.location || 'Remote'}</span>
                        </div>
                      </td>

                      {/* Skills Stack */}
                      <td>
                        <div className="skill-chips-container">
                          {skillsList.slice(0, 4).map((s, idx) => (
                            <span key={idx} className="skill-chip">{String(s).trim()}</span>
                          ))}
                          {skillsList.length > 4 && (
                            <span className="skill-chip" style={{ opacity: 0.7 }}>+{skillsList.length - 4}</span>
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
                          title="Direct application on source portal"
                        >
                          <Send size={12} />
                          <span>Apply</span>
                        </a>
                      </td>

                      {/* Trust Audit */}
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.785rem' }}
                          onClick={() => onInspectProvenance(r.id)}
                          title="View Jev Anti-Ghost & Traceability Proof"
                        >
                          <ShieldCheck size={14} color="var(--accent-cyan)" />
                          <span>Audit</span>
                        </button>
                      </td>
                    </tr>
                  );
                }

                // Standard fallback rendering for non-job datasets
                return (
                  <tr key={r.id}>
                    <td>
                      <span className={`confidence-pill ${confClass}`}>
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
                        <ShieldCheck size={14} color="var(--accent-cyan)" />
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
