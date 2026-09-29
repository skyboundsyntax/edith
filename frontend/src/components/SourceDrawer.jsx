import React, { useState, useEffect } from 'react';
import { X, ExternalLink, ShieldCheck, CheckCircle2, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

export default function SourceDrawer({ recordId, onClose, onRecordUpdated }) {
  const [provenance, setProvenance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);

  useEffect(() => {
    if (!recordId) return;
    let isMounted = true;
    api.getRecordProvenance(recordId)
      .then((data) => {
        if (isMounted) {
          setProvenance(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error(err);
        if (isMounted) setLoading(false);
      });
    return () => { isMounted = false; };
  }, [recordId]);

  const handleReviewAction = async (action) => {
    setReviewing(true);
    try {
      await api.reviewRecord(recordId, action);
      if (onRecordUpdated) onRecordUpdated();
      onClose();
    } catch (err) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setReviewing(false);
    }
  };

  if (!recordId) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <ShieldCheck size={22} color="var(--accent-emerald)" />
            <h2 className="drawer-title">Data Lineage & Traceability Audit (SDD Section 3)</h2>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Retrieving source-backed provenance audit trail...
          </div>
        ) : !provenance ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-rose)' }}>
            Failed to load record provenance.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Record Identity & Origin Source URL */}
            <div className="glass-panel" style={{ padding: '1rem 1.25rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                ORIGIN URL METADATA (LANGCHAIN DOCUMENT BINDING)
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.35rem' }}>
                <a
                  href={provenance.source?.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: 'var(--text-amber)',
                    fontWeight: 600,
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    wordBreak: 'break-all'
                  }}
                >
                  <ExternalLink size={15} />
                  <span>{provenance.source?.url}</span>
                </a>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                Captured Timestamp: {provenance.source?.captured_timestamp || 'N/A'} • Source Title: {provenance.source?.title || 'Web Intelligence'}
              </div>
            </div>

            {/* Jev's Job Trust Meter & Anti-Ghost Evaluation */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Jev's Job Trust Meter & Anti-Ghost Legitimacy Audit
                </span>
                <span
                  className="trust-meter-badge high"
                  style={{
                    background: provenance.confidence_evaluation?.overall_score >= 80 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                    color: provenance.confidence_evaluation?.overall_score >= 80 ? '#34d399' : '#f87171',
                    border: `1px solid ${provenance.confidence_evaluation?.overall_score >= 80 ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`
                  }}
                >
                  {provenance.confidence_evaluation?.overall_score}% Trust Score
                </span>
              </div>

              {/* Anti-Ghost Verification Banner */}
              <div style={{ marginTop: '0.75rem' }} className={`anti-ghost-banner ${provenance.confidence_evaluation?.overall_score >= 80 ? '' : 'warning'}`}>
                {provenance.confidence_evaluation?.overall_score >= 80 ? (
                  <CheckCircle2 size={18} color="#34d399" />
                ) : (
                  <AlertTriangle size={18} color="#f87171" />
                )}
                <div>
                  <strong>{provenance.confidence_evaluation?.overall_score >= 80 ? 'Verified Legit & Active Listing' : 'Caution: Suspect / Stale Job Notice'}</strong>
                  <div style={{ fontSize: '0.75rem', opacity: 0.85 }}>
                    {provenance.confidence_evaluation?.overall_score >= 80
                      ? 'Verified on public career portal with grounded company tokens and authentic application destination.'
                      : 'Flagged for review: Potential undisclosed compensation, third-party recruiter re-post, or missing direct apply credentials.'}
                  </div>
                </div>
              </div>

              <div className="score-breakdown-grid" style={{ marginTop: '0.75rem' }}>
                <div className="breakdown-card">
                  <div className="breakdown-metric-title">Source Grounding (40%)</div>
                  <div className="breakdown-metric-score" style={{ color: 'var(--text-emerald)' }}>
                    {provenance.confidence_evaluation?.breakdown?.source_grounding || 0}%
                  </div>
                </div>
                <div className="breakdown-card">
                  <div className="breakdown-metric-title">Role & Stack Match (30%)</div>
                  <div className="breakdown-metric-score" style={{ color: 'var(--accent-indigo)' }}>
                    {provenance.confidence_evaluation?.breakdown?.completeness || 0}%
                  </div>
                </div>
                <div className="breakdown-card">
                  <div className="breakdown-metric-title">Direct Apply Integrity (20%)</div>
                  <div className="breakdown-metric-score" style={{ color: 'var(--text-amber)' }}>
                    {provenance.confidence_evaluation?.breakdown?.syntax_validity || 0}%
                  </div>
                </div>
                <div className="breakdown-card">
                  <div className="breakdown-metric-title">Platform Authenticity (10%)</div>
                  <div className="breakdown-metric-score" style={{ color: 'var(--text-primary)' }}>
                    {provenance.confidence_evaluation?.breakdown?.information_density || 0}%
                  </div>
                </div>
              </div>
            </div>

            {/* Raw Extracted Snippet Citation */}
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                RAW SOURCE SNIPPET CITATION (ORIGIN WEBPAGE CONTENT)
              </div>
              <div className="snippet-box">
                {provenance.source?.raw_snippet || 'No raw snippet captured.'}
              </div>
            </div>

            {/* Extracted Structured JSON Payload */}
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                PERSISTED STRUCTURED JSON PAYLOAD
              </div>
              <pre
                style={{
                  background: '#04070d',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1rem',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8rem',
                  color: '#93c5fd',
                  overflowX: 'auto',
                  maxHeight: '160px'
                }}
              >
                {JSON.stringify(provenance.payload, null, 2)}
              </pre>
            </div>

            {/* Human Review Resolution */}
            {provenance.confidence_evaluation?.human_review_required && (
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '1rem'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <AlertTriangle size={20} color="var(--accent-rose)" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-rose)' }}>
                      Human Review Loop Triggered
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      Confidence score &lt; 80% threshold. Verify before enterprise ingestion.
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-primary"
                    style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
                    onClick={() => handleReviewAction('approve')}
                    disabled={reviewing}
                  >
                    <CheckCircle2 size={14} />
                    <span>Approve</span>
                  </button>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
                    onClick={() => handleReviewAction('reject')}
                    disabled={reviewing}
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
