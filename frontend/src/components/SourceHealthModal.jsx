import React, { useState, useEffect, useCallback } from 'react';
import { X, ShieldCheck, Activity, Globe, ExternalLink, RefreshCw, CheckCircle2, AlertTriangle, Radio } from 'lucide-react';
import { api } from '../services/api';

export default function SourceHealthModal({ isOpen, onClose }) {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ total: 0, online: 0, linkout: 0 });

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSourcesHealth();
      setSources(data.sources || []);
      setStats({
        total: data.total_sources || 0,
        online: data.online_sources || 0,
        linkout: data.linkout_sources || 0
      });
    } catch (err) {
      console.error('Failed to load sources health:', err);
      setError(err?.message || 'Unable to retrieve source health telemetry.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchHealth();
    }
  }, [isOpen, fetchHealth]);

  // Keyboard navigation: Escape key closes modal
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label="Source Policy Registry">
      <div className="modal-container" style={{ maxWidth: '850px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Activity size={20} color="var(--accent-amber)" />
            <div>
              <h2 style={{ fontSize: '1.15rem', margin: 0, fontWeight: 600 }}>Source Policy Registry & Health Matrix</h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Legal compliance, robots policies & real-time connection status
              </span>
            </div>
          </div>
          <button className="btn-icon" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
          {/* Top Summary Banner */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.25rem' }}>
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.25)', padding: '0.85rem', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <CheckCircle2 size={13} /> LIVE CONNECTORS
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#ffffff', marginTop: '0.2rem' }}>
                {stats.online} Active
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Public ATS & REST Endpoints</div>
            </div>

            <div style={{ background: 'oklch(62% 0.16 272 / 0.12)', border: '1px solid oklch(62% 0.16 272 / 0.3)', padding: '0.85rem', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-indigo)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Radio size={13} /> LINK-OUT CHANNELS
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#ffffff', marginTop: '0.2rem' }}>
                {stats.linkout} Platforms
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Restricted (Direct Navigation)</div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)', padding: '0.85rem', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <ShieldCheck size={13} /> ETHICAL SCRAPING
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#ffffff', marginTop: '0.2rem' }}>
                100%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>No CAPTCHA / Login Bypasses</div>
            </div>
          </div>

          {error ? (
            <div style={{ padding: '2.5rem', textAlign: 'center' }}>
              <AlertTriangle size={32} color="var(--accent-rose)" style={{ margin: '0 auto 0.75rem auto' }} />
              <p style={{ color: '#f87171', fontSize: '0.9rem', marginBottom: '1rem' }}>{error}</p>
              <button type="button" className="btn btn-secondary" onClick={fetchHealth}>
                <RefreshCw size={14} style={{ marginRight: '0.35rem' }} />
                <span>Retry Health Matrix Check</span>
              </button>
            </div>
          ) : (
            /* Sources Table */
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Provider / Domain</th>
                    <th>Access Method</th>
                    <th>Status</th>
                    <th>Latency</th>
                    <th>Permission & Robots Policy</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map((s) => {
                    const isOnline = s.status === 'ONLINE';
                    const isLinkOut = s.status === 'LINK_OUT_ONLY';
                    return (
                      <tr key={s.id}>
                        <td>
                          <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.88rem' }}>{s.name}</div>
                          <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>{s.domain}</div>
                        </td>
                        <td>
                          <span style={{
                            fontSize: '0.72rem',
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                            background: isLinkOut ? 'oklch(62% 0.16 272 / 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            color: isLinkOut ? 'var(--text-indigo)' : '#34d399',
                            fontWeight: 500
                          }}>
                            {s.access_method}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                            <span style={{
                              width: '8px',
                              height: '8px',
                              borderRadius: '50%',
                              background: isOnline ? '#10b981' : isLinkOut ? '#6366f1' : '#f59e0b'
                            }} />
                            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: isOnline ? '#34d399' : isLinkOut ? '#a5b4fc' : '#fbbf24' }}>
                              {s.status}
                            </span>
                          </div>
                        </td>
                        <td style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-amber)' }}>
                          {s.latency_ms > 0 ? `${s.latency_ms}ms` : '—'}
                        </td>
                        <td style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', maxWidth: '320px', lineHeight: 1.35 }}>
                          {s.robots_policy}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={fetchHealth}
            disabled={loading}
            style={{ fontSize: '0.8rem' }}
          >
            <RefreshCw size={13} style={{ marginRight: '0.35rem', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            <span>Refresh Health Status</span>
          </button>
          <button type="button" className="btn btn-primary" onClick={onClose} style={{ fontSize: '0.85rem' }}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
