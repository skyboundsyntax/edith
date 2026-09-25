import React, { useState, useMemo } from 'react';
import { Search, ExternalLink, ShieldCheck, Filter, FileSpreadsheet, FileCode } from 'lucide-react';

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
    if (score >= 85) return 'high';
    return 'medium';
  };

  return (
    <div className="glass-panel data-grid-section">
      <div className="grid-toolbar">
        {/* Search Input */}
        <div className="toolbar-search">
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search records, entities, or sources..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Filters and Actions */}
        <div className="toolbar-actions">
          {/* Min Confidence Slider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <Filter size={14} />
            <span>Min Confidence: {minConfidenceFilter}%</span>
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
            Review Flagged ({records.filter((r) => r.human_review_required).length})
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
            <tr>
              <th>CONFIDENCE (JEV)</th>
              {dynamicColumns.slice(0, 4).map((col) => (
                <th key={col.key}>{col.label}</th>
              ))}
              <th>VERIFIED SOURCE</th>
              <th style={{ textAlign: 'right' }}>PROVENANCE AUDIT</th>
            </tr>
          </thead>
          <tbody>
            {filteredRecords.length === 0 ? (
              <tr>
                <td colSpan={dynamicColumns.length + 3} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  No records matching the filter criteria.
                </td>
              </tr>
            ) : (
              filteredRecords.map((r) => {
                const confClass = getConfidenceClass(r.confidence_score, r.human_review_required);
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
