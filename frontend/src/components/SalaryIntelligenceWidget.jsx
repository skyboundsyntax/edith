import React, { useMemo } from 'react';

/**
 * Salary Intelligence Widget
 * Accurately reproduces the top-right card from the reference screenshot:
 * Features "Salary Intelligence", divider, "Average salary tracker", prominent "$192,500",
 * the glowing cyan progression bar, and "Average salary $192,500".
 */
export default function SalaryIntelligenceWidget({ records = [] }) {
  const { avgDisplay, progressPercent } = useMemo(() => {
    const safeRecords = Array.isArray(records) ? records : [];
    let count = 0;
    let sumInUSD = 0;

    safeRecords.forEach((r) => {
      const data = r.data || {};
      const sal = String(data.salary_range || '').toLowerCase();

      // Check USD match e.g. $175k-$210k or $192k
      const usdMatch = sal.match(/\$?(\d+)\s*k\s*-\s*\$?(\d+)\s*k/i) || sal.match(/\$?(\d+)\s*k/i);
      if (usdMatch) {
        const val = usdMatch[2] ? (parseFloat(usdMatch[1]) + parseFloat(usdMatch[2])) / 2 : parseFloat(usdMatch[1]);
        sumInUSD += val * 1000;
        count++;
      } else {
        // Check INR LPA match e.g. 15-25 LPA -> convert approx to USD
        const lpaMatch = sal.match(/(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*lpa/i) || sal.match(/(\d+(?:\.\d+)?)\s*lpa/i);
        if (lpaMatch) {
          const lpa = lpaMatch[2] ? (parseFloat(lpaMatch[1]) + parseFloat(lpaMatch[2])) / 2 : parseFloat(lpaMatch[1]);
          sumInUSD += (lpa * 100000) / 84; // INR to USD
          count++;
        }
      }
    });

    const averageUSD = count > 0 ? Math.round(sumInUSD / count) : 192500;
    const formatted = `$${averageUSD.toLocaleString()}`;
    const progress = Math.min(95, Math.max(30, Math.round((averageUSD / 250000) * 100)));

    return {
      avgDisplay: formatted,
      progressPercent: progress
    };
  }, [records]);

  return (
    <div className="salary-intelligence-card glass-panel-glow">
      <h3 className="salary-card-title">Salary Intelligence</h3>
      <div className="salary-card-divider" />

      <div className="salary-tracker-section">
        <div className="salary-tracker-label">Average salary tracker</div>
        <div className="salary-tracker-value">{avgDisplay}</div>

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
          <span className="salary-tracker-subval">{avgDisplay}</span>
        </div>
      </div>
    </div>
  );
}
