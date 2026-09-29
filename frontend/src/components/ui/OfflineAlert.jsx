import React from 'react';
import { WifiOff, AlertTriangle, RefreshCw, X } from 'lucide-react';

/**
 * Offline & Network Recovery Banner
 * Satisfies resilient error recovery and network degradation hardening.
 */
export default function OfflineAlert({
  error,
  onRetry,
  onDismiss,
  isRetrying = false
}) {
  if (!error) return null;

  return (
    <div
      className="offline-alert-banner glass-panel"
      role="alert"
      aria-live="assertive"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.85rem',
        padding: '0.85rem 1.25rem',
        margin: '0.75rem 0',
        borderRadius: '14px',
        background: 'rgba(239, 68, 68, 0.15)',
        border: '1.5px solid rgba(239, 68, 68, 0.45)',
        backdropFilter: 'blur(20px)',
        color: '#fecaca'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
        <div
          style={{
            padding: '0.45rem',
            borderRadius: '8px',
            background: 'rgba(239, 68, 68, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}
        >
          <WifiOff size={18} color="#f87171" aria-hidden="true" />
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: '0.875rem', color: '#fca5a5' }}>
            Pipeline Connectivity Warning
          </div>
          <div
            style={{
              fontSize: '0.785rem',
              color: '#cbd5e1',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: '650px'
            }}
            title={typeof error === 'string' ? error : error.message}
          >
            {typeof error === 'string' ? error : (error.message || 'Failed to reach intelligence backend. Check server daemon status.')}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {onRetry && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onRetry}
            disabled={isRetrying}
            style={{
              fontSize: '0.75rem',
              padding: '0.35rem 0.75rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              borderRadius: '8px',
              border: '1px solid rgba(239, 68, 68, 0.5)',
              background: 'rgba(239, 68, 68, 0.2)',
              color: '#ffffff'
            }}
          >
            <RefreshCw size={12} className={isRetrying ? 'animate-spin' : ''} />
            <span>{isRetrying ? 'Retrying...' : 'Retry Connection'}</span>
          </button>
        )}

        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '0.25rem',
              display: 'flex',
              alignItems: 'center'
            }}
            aria-label="Dismiss error notice"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
