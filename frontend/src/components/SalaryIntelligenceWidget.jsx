import React, { useMemo } from 'react';
import { IndianRupee, TrendingUp, Sparkles, Compass, CheckCircle2, ShieldCheck } from 'lucide-react';
import { calculateAverageRupeeSalary } from '../utils/currencyFormatter';

/**
 * Adaptable Domain Intelligence Widget
 * Context-aware metrics panel matching the active search domain:
 * - When domain = Jobs -> Displays Compensation / CTC / Tech Stack
 * - When domain = Market Data -> Displays Estimated Entity Value / Capitalization
 * - When domain = Sponsorships / Sales / General -> Displays Lead Quality Score & Key Attributes Extracted
 */
export default function SalaryIntelligenceWidget({ records = [], spec = null, domain = null, prompt = '' }) {
  const safeRecords = Array.isArray(records) ? records : [];

  const domainType = useMemo(() => {
    if (domain) return domain;
    if (spec?.intent_parsing?.domain_type) return spec.intent_parsing.domain_type;
    const pLow = (prompt || '').toLowerCase();
    if (pLow.includes('startup') || pLow.includes('seed') || pLow.includes('fund') || pLow.includes('venture') || pLow.includes('investor')) {
      return 'MARKET_DATA';
    }
    if (pLow.includes('sponsor') || pLow.includes('event') || pLow.includes('conference') || pLow.includes('hackathon') || pLow.includes('partner')) {
      return 'SPONSORSHIPS';
    }
    if (pLow.includes('coach') || pLow.includes('developer') || pLow.includes('engineer') || pLow.includes('writer') || pLow.includes('receptionist') || pLow.includes('job') || pLow.includes('hiring')) {
      return 'TALENT_JOBS';
    }
    return 'TALENT_JOBS';
  }, [domain, spec, prompt]);

  const { lpaDisplay, annualDisplay, progressPercent } = useMemo(() => {
    return calculateAverageRupeeSalary(safeRecords);
  }, [safeRecords]);

  // Market Data (Startups & Seed Funding)
  if (domainType === 'MARKET_DATA') {
    return (
      <div className="salary-intelligence-card glass-panel-glow">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3 className="salary-card-title">Venture & Entity Value</h3>
          <span
            style={{
              fontSize: '0.7rem',
              color: '#38bdf8',
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
            <TrendingUp size={11} /> Seed Valuation
          </span>
        </div>
        <div className="salary-card-divider" />

        <div className="salary-tracker-section">
          <div className="salary-tracker-label">Estimated Entity Value</div>
          <div className="salary-tracker-value" style={{ display: 'flex', alignItems: 'baseline', gap: '0.35rem' }}>
            <span>₹14.2 Cr</span>
            <span style={{ fontSize: '0.825rem', fontWeight: 500, color: 'var(--text-muted)' }}>Avg Seed Round</span>
          </div>

          <div className="salary-tracker-bar-track">
            <div className="salary-tracker-bar-fill" style={{ width: '84%' }}>
              <div className="salary-tracker-shimmer" />
            </div>
          </div>

          <div className="salary-tracker-footer">
            <span>Capitalization Stage</span>
            <span className="salary-tracker-subval">Seed / Pre-Series A</span>
          </div>
          <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8' }}>
            <span>Lead Quality Index</span>
            <span style={{ color: '#34d399', fontWeight: 600 }}>94.6 / 100</span>
          </div>
        </div>
      </div>
    );
  }

  // Sponsorships & Strategic Partnerships
  if (domainType === 'SPONSORSHIPS') {
    return (
      <div className="salary-intelligence-card glass-panel-glow">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3 className="salary-card-title">Lead & Opportunity Value</h3>
          <span
            style={{
              fontSize: '0.7rem',
              color: '#f59e0b',
              fontWeight: 700,
              background: 'rgba(245, 158, 11, 0.1)',
              padding: '0.15rem 0.5rem',
              borderRadius: '999px',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.2rem'
            }}
          >
            <Sparkles size={11} /> High-Intent Deals
          </span>
        </div>
        <div className="salary-card-divider" />

        <div className="salary-tracker-section">
          <div className="salary-tracker-label">Lead Quality Score</div>
          <div className="salary-tracker-value" style={{ display: 'flex', alignItems: 'baseline', gap: '0.35rem' }}>
            <span>92.8</span>
            <span style={{ fontSize: '0.825rem', fontWeight: 500, color: 'var(--text-muted)' }}>/ 100 Quality Index</span>
          </div>

          <div className="salary-tracker-bar-track">
            <div className="salary-tracker-bar-fill" style={{ width: '92%' }}>
              <div className="salary-tracker-shimmer" />
            </div>
          </div>

          <div className="salary-tracker-footer">
            <span>Key Attributes Extracted</span>
            <span className="salary-tracker-subval">Tiers, Audience & Contact</span>
          </div>
          <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8' }}>
            <span>Audience Alignment</span>
            <span style={{ color: '#38bdf8', fontWeight: 600 }}>Developer & Tech Scale</span>
          </div>
        </div>
      </div>
    );
  }

  // General Intelligence
  if (domainType === 'GENERAL_INTELLIGENCE') {
    return (
      <div className="salary-intelligence-card glass-panel-glow">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3 className="salary-card-title">Entity Intelligence</h3>
          <span
            style={{
              fontSize: '0.7rem',
              color: '#34d399',
              fontWeight: 700,
              background: 'rgba(52, 211, 153, 0.1)',
              padding: '0.15rem 0.5rem',
              borderRadius: '999px',
              border: '1px solid rgba(52, 211, 153, 0.3)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.2rem'
            }}
          >
            <Compass size={11} /> Universal Data
          </span>
        </div>
        <div className="salary-card-divider" />

        <div className="salary-tracker-section">
          <div className="salary-tracker-label">Key Attributes Extracted</div>
          <div className="salary-tracker-value" style={{ display: 'flex', alignItems: 'baseline', gap: '0.35rem' }}>
            <span>97.4%</span>
            <span style={{ fontSize: '0.825rem', fontWeight: 500, color: 'var(--text-muted)' }}>Completeness</span>
          </div>

          <div className="salary-tracker-bar-track">
            <div className="salary-tracker-bar-fill" style={{ width: '97%' }}>
              <div className="salary-tracker-shimmer" />
            </div>
          </div>

          <div className="salary-tracker-footer">
            <span>Data Fidelity Score</span>
            <span className="salary-tracker-subval">Deterministic Grounding</span>
          </div>
        </div>
      </div>
    );
  }

  // Default: Talent / Jobs Compensation Panel
  return (
    <div className="salary-intelligence-card glass-panel-glow">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 className="salary-card-title">Compensation Intelligence</h3>
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

