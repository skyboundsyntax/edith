import React from 'react';
import { IndianRupee, CheckCircle2, X, Filter } from 'lucide-react';

const SALARY_BRACKETS = [
  { id: 'ALL', label: 'All CTC', range: null },
  { id: '6-12', label: '₹6 - 12 LPA', min: 6, max: 12 },
  { id: '12-20', label: '₹12 - 20 LPA', min: 12, max: 20 },
  { id: '20-30', label: '₹20 - 30 LPA', min: 20, max: 30 },
  { id: '30-40', label: '₹30 - 40 LPA', min: 30, max: 40 },
  { id: '40+', label: '₹40+ LPA', min: 40, max: null }
];

export default function SalaryBracketFilterBar({
  activeBracket = 'ALL',
  onSelectBracket,
  detectedQueryBracket = null,
  onClearQueryBracket
}) {
  const isQueryDriven = Boolean(detectedQueryBracket?.hasSalaryFilter);

  return (
    <div
      className="glass-panel salary-bracket-filter-bar"
      style={{
        marginTop: '0.75rem',
        padding: '0.65rem 1rem',
        borderRadius: '14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        background: 'rgba(12, 22, 36, 0.55)',
        border: '1px solid rgba(86, 204, 242, 0.2)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--accent-amber)', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em' }}>
          <IndianRupee size={14} />
          <span>CTC BRACKET:</span>
        </div>

        {isQueryDriven ? (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'rgba(245, 158, 11, 0.16)',
              border: '1px solid var(--accent-amber)',
              color: '#fbbf24',
              padding: '0.25rem 0.75rem',
              borderRadius: '20px',
              fontSize: '0.785rem',
              fontWeight: 700
            }}
          >
            <span>
              Search Bracket: ₹{detectedQueryBracket.minLpa}
              {detectedQueryBracket.maxLpa ? ` - ${detectedQueryBracket.maxLpa}` : '+'} LPA
            </span>
            {onClearQueryBracket && (
              <button
                type="button"
                onClick={onClearQueryBracket}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#fbbf24',
                  cursor: 'pointer',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center'
                }}
                title="Clear query salary bracket"
                aria-label="Clear query salary bracket"
              >
                <X size={13} />
              </button>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
            {SALARY_BRACKETS.map((b) => {
              const isActive = activeBracket === b.id;
              return (
                <button
                  key={b.id}
                  type="button"
                  onClick={() => onSelectBracket && onSelectBracket(b.id)}
                  style={{
                    background: isActive ? 'rgba(245, 158, 11, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                    border: `1px solid ${isActive ? 'var(--accent-amber)' : 'rgba(255, 255, 255, 0.08)'}`,
                    color: isActive ? '#fbbf24' : 'var(--text-secondary)',
                    padding: '0.25rem 0.65rem',
                    borderRadius: '8px',
                    fontSize: '0.765rem',
                    fontWeight: isActive ? 700 : 500,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {b.label}
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', color: '#94a3b8' }}>
        <CheckCircle2 size={12} color="#10b981" />
        <span>Desired bracket + unlisted roles • zero roles outside bracket</span>
      </div>
    </div>
  );
}
