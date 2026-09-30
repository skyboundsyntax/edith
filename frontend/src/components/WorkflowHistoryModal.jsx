import React, { useEffect } from 'react';
import { X, Layers, CheckCircle2, Clock, ArrowRight } from 'lucide-react';
import { truncateSafe } from '../utils/urlValidator';

export default function WorkflowHistoryModal({
  isOpen,
  onClose,
  workflows = [],
  activeWorkflowId,
  onSelectWorkflow
}) {
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

  const formatDate = (isoString) => {
    if (!isoString) return 'Active session';
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return 'Recently';
      return new Intl.DateTimeFormat('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short'
      }).format(d);
    } catch {
      return 'Recently';
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label="Workflow Execution History">
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '640px' }}>
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Layers size={22} color="var(--accent-amber)" />
            <h2 className="drawer-title">Workflow Execution History</h2>
          </div>
          <button className="close-btn" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', maxHeight: '65vh', overflowY: 'auto' }}>
          {workflows.length === 0 ? (
            <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No workflow history yet. Run a prompt to see executions here.
            </div>
          ) : (
            workflows.map((wf) => {
              const isActive = wf.id === activeWorkflowId;
              const count = wf.total_deduplicated ?? wf.total_extracted ?? 0;
              return (
                <div
                  key={wf.id}
                  className="glass-panel"
                  style={{
                    padding: '1rem 1.25rem',
                    cursor: 'pointer',
                    borderColor: isActive ? 'var(--accent-amber)' : 'var(--border-subtle)',
                    background: isActive ? 'var(--bg-glass-active)' : 'var(--bg-glass-card)'
                  }}
                  onClick={() => {
                    onSelectWorkflow(wf.id);
                    onClose();
                  }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onSelectWorkflow(wf.id);
                      onClose();
                    }
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                        {wf.status === 'completed' ? (
                          <CheckCircle2 size={16} color="var(--accent-emerald)" />
                        ) : (
                          <Clock size={16} color="var(--accent-amber)" />
                        )}
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                          {wf.id} • {wf.status}
                        </span>
                      </div>
                      <div
                        className="wrap-resilient"
                        dir="auto"
                        style={{ fontSize: '0.925rem', fontWeight: 600, color: 'var(--text-primary)' }}
                        title={wf.prompt}
                      >
                        {truncateSafe(wf.prompt || 'Untitled Ingestion Pipeline', 120)}
                      </div>
                      <div style={{ fontSize: '0.785rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                        {count} records extracted • {formatDate(wf.created_at)}
                      </div>
                    </div>

                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem', flexShrink: 0 }}
                      aria-label={`Load workflow ${wf.id}`}
                    >
                      <span>Load</span>
                      <ArrowRight size={13} />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
