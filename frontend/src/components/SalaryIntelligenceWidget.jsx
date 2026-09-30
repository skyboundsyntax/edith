import React, { useMemo } from 'react';
import { IndianRupee } from 'lucide-react';
import { calculateAverageRupeeSalary } from '../utils/currencyFormatter';

/**
 * Salary Intelligence Widget
 * Real-time compensation intelligence calibrated in Indian Rupees (₹) & LPA:
 * Displays Average salary tracker (e.g. ₹18.5 LPA), glowing cyan progression bar,
 * and annual CTC breakdown.
 */
export default function SalaryIntelligenceWidget({ records = [] }) {
  const { lpaDisplay, annualDisplay, progressPercent, sampleCount } = useMemo(() => {
    return calculateAverageRupeeSalary(records);
  }, [records]);

  return (
    <div className="salary-intelligence-card glass-panel-glow">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 className="salary-card-title">Salary Intelligence</h3>
        <span
          style={{
            fontSize: '0.7rem',
            color: 'var(--text-cyan)',
            fontWeight: 700,
            background: 'rgba(56, 189, 248, 0.1)',
            padding: '0.15rem 0.5rem',
            borderRadius: '999px',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.2rem'
          }}
        >
          <IndianRupee size={10} /> INR Standard
        </span>
      </div>
      <div className="salary-card-divider" />

      <div className="salary-tracker-section">
        <div className="salary-tracker-label">Average salary tracker</div>
        <div className="salary-tracker-value" style={{ display: 'flex', alignItems: 'baseline', gap: '0.35rem' }}>
          <span>{lpaDisplay}</span>
          <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)' }}>CTC</span>
        </div>

        <div className="salary-tracker-bar-track">
          <div
            className="salary-tracker-bar-fill"
            style={{ width: `${progressPercent}%` }}
          >
            <div className="salary-tracker-shimmer" />
          </div>
        </div>

        <div className="salary-tracker-footer">
          <span>Average salary</span>
          <span className="salary-tracker-subval">{annualDisplay}</span>
        </div>
      </div>
    </div>
  );
}

