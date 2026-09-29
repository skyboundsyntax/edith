import React from 'react';

/**
 * Reusable Stat Monolith Component
 * Extracted from Executive Tech Dossier for high-impact metric presentation.
 * Resilient against extreme text lengths, international currencies, and null values.
 */
export default function StatMonolith({
  icon: Icon,
  label,
  value,
  unit,
  subtext,
  theme = 'amber',
  className = ''
}) {
  const displayVal = value !== null && value !== undefined && value !== ''
    ? value
    : 'N/A';

  const themeClass =
    theme === 'emerald'
      ? 'fit-glow'
      : theme === 'cyan'
        ? 'mode-text online'
        : 'salary-glow';

  return (
    <div
      className={`dossier-stat-monolith theme-${theme} ${className}`}
      style={{ minWidth: 0, overflow: 'hidden' }}
    >
      <div className="monolith-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', minWidth: 0 }}>
        {Icon && <Icon size={13} style={{ flexShrink: 0 }} aria-hidden="true" />}
        <span
          style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}
        >
          {label}
        </span>
      </div>

      <div
        className={`monolith-hero-val ${themeClass}`}
        dir="auto"
        style={{
          wordBreak: 'break-word',
          overflowWrap: 'break-word',
          lineHeight: 1.15
        }}
      >
        <span>{displayVal}</span>
        {unit && (
          <span
            className="monolith-unit"
            style={{
              fontSize: '0.45em',
              fontWeight: 700,
              marginLeft: '0.35rem',
              letterSpacing: '0.05em',
              opacity: 0.8
            }}
          >
            {unit}
          </span>
        )}
      </div>

      {subtext && (
        <div
          className="monolith-subtext"
          style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            lineHeight: 1.3
          }}
          title={subtext}
        >
          {subtext}
        </div>
      )}
    </div>
  );
}
