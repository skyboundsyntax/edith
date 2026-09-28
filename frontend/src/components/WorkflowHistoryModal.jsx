import React from 'react';
import { X, Layers, CheckCircle2, Clock, ArrowRight } from 'lucide-react';

export default function WorkflowHistoryModal({
  isOpen,
  onClose,
  workflows = [],
  activeWorkflowId,
  onSelectWorkflow
}) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '640px' }}>
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Layers size={22} color="var(--accent-cyan)" />
            <h2 className="drawer-title">Workflow Execution History</h2>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {workflows.length === 0 ? (
            <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No workflow history yet. Run a prompt to see executions here.
            </div>
          ) : (
            workflows.map((wf) => {
              const isActive = wf.id === activeWorkflowId;
              return (
                <div
                  key={wf.id}
                  className="glass-panel"
                  style={{
                    padding: '1rem 1.25rem',
                    cursor: 'pointer',
                    borderColor: isActive ? 'var(--accent-cyan)' : 'var(--border-subtle)',
                    background: isActive ? 'var(--bg-glass-active)' : 'var(--bg-glass-card)'
                  }}
                  onClick={() => {
                    onSelectWorkflow(wf.id);
                    onClose();
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                        {wf.status === 'completed' ? (
                          <CheckCircle2 size={16} color="var(--accent-emerald)" />
                        ) : (
                          <Clock size={16} color="var(--accent-cyan)" />
                        )}
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                          {wf.id} • {wf.status}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.925rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {wf.prompt}
                      </div>
                      <div style={{ fontSize: '0.785rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                        {wf.total_deduplicated || wf.total_extracted} records extracted • {wf.created_at ? new Date(wf.created_at).toLocaleString() : ''}
                      </div>
                    </div>

                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
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
