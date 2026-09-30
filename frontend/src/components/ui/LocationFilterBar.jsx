import React from 'react';
import { MapPin, Globe, Building2, Filter, Zap } from 'lucide-react';

const PUNE_KEYWORDS = [
  'pune', 'hinjewadi', 'hinjawadi', 'magarpatta', 'kharadi',
  'viman nagar', 'baner', 'wakad', 'hadapsar', 'kothrud',
  'aundh', 'yerwada', 'kalyani nagar', 'balewadi', 'bhosari', 'chakan', 'shivajinagar'
];

export const isJobInPune = (job) => {
  const d = job?.data || {};
  const loc = (d.location || '').toLowerCase();
  const city = (d.city || '').toLowerCase();
  const title = (d.job_title || job?.source_title || '').toLowerCase();
  const desc = (d.description || d.raw_snippet || '').toLowerCase().slice(0, 400);

  return PUNE_KEYWORDS.some((kw) =>
    loc.includes(kw) || city.includes(kw) || title.includes(kw) || desc.includes(`in ${kw}`)
  );
};

export const isJobInBengaluru = (job) => {
  const d = job?.data || {};
  const loc = (d.location || '').toLowerCase();
  const city = (d.city || '').toLowerCase();
  const blr = ['bangalore', 'bengaluru', 'blr', 'whitefield', 'electronic city', 'koramangala', 'bellandur', 'indiranagar'];
  return blr.some((kw) => loc.includes(kw) || city.includes(kw));
};

export const isJobInMumbai = (job) => {
  const d = job?.data || {};
  const loc = (d.location || '').toLowerCase();
  const city = (d.city || '').toLowerCase();
  const bom = ['mumbai', 'bombay', 'navi mumbai', 'thane', 'bkc', 'andheri', 'powai', 'bandra'];
  return bom.some((kw) => loc.includes(kw) || city.includes(kw));
};

export const isJobInDelhiNCR = (job) => {
  const d = job?.data || {};
  const loc = (d.location || '').toLowerCase();
  const city = (d.city || '').toLowerCase();
  const del = ['delhi', 'new delhi', 'ncr', 'gurgaon', 'gurugram', 'noida'];
  return del.some((kw) => loc.includes(kw) || city.includes(kw));
};

export const isJobInHyderabad = (job) => {
  const d = job?.data || {};
  const loc = (d.location || '').toLowerCase();
  const city = (d.city || '').toLowerCase();
  const hyd = ['hyderabad', 'secunderabad', 'hitech city', 'gachibowli', 'madhapur', 'kondapur'];
  return hyd.some((kw) => loc.includes(kw) || city.includes(kw));
};

export const isJobOnlineRemote = (job) => {
  const d = job?.data || {};
  const rawModality = String(d.work_modality || '').toLowerCase();
  const remoteType = String(d.remote_type || '').toLowerCase();
  const locLower = String(d.location || '').toLowerCase();
  return (
    rawModality === 'online' ||
    remoteType === 'remote' ||
    /remote|online|virtual|wfh|telecommute/i.test(locLower)
  );
};

export const isJobOfflineOnSite = (job) => {
  return !isJobOnlineRemote(job);
};

export default function LocationFilterBar({
  activeFilter = 'ALL',
  onSelectFilter,
  records = [],
  onScrapePune,
  isRunning = false
}) {
  const counts = React.useMemo(() => {
    let pune = 0;
    let blr = 0;
    let mum = 0;
    let del = 0;
    let hyd = 0;
    let remote = 0;
    let offline = 0;

    for (const r of records) {
      if (isJobInPune(r)) pune++;
      if (isJobInBengaluru(r)) blr++;
      if (isJobInMumbai(r)) mum++;
      if (isJobInDelhiNCR(r)) del++;
      if (isJobInHyderabad(r)) hyd++;
      if (isJobOnlineRemote(r)) remote++;
      else offline++;
    }

    return { all: records.length, pune, blr, mum, del, hyd, remote, offline };
  }, [records]);

  const FILTERS = [
    { id: 'ALL', label: '🇮🇳 All India', sublabel: 'Pan-India & Remote', icon: Globe, count: counts.all },
    { id: 'BLR', label: 'Bengaluru', icon: MapPin, count: counts.blr },
    { id: 'PUNE', label: 'Pune', icon: MapPin, count: counts.pune },
    { id: 'MUM', label: 'Mumbai', icon: MapPin, count: counts.mum },
    { id: 'DEL', label: 'Delhi NCR', icon: MapPin, count: counts.del },
    { id: 'HYD', label: 'Hyderabad', icon: MapPin, count: counts.hyd },
    { id: 'REMOTE', label: '🟢 Online / Remote', icon: Globe, count: counts.remote },
    { id: 'OFFLINE', label: '🏢 Offline / On-Site', icon: Building2, count: counts.offline },
  ];

  return (
    <div
      className="location-filter-bar glass-panel"
      role="toolbar"
      aria-label="Filter vacancies by geographic location and work modality"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.65rem',
        padding: '0.65rem 1rem',
        borderRadius: '14px',
        margin: '0.75rem 0 1rem 0',
        background: 'rgba(11, 20, 36, 0.65)',
        border: '1px solid rgba(86, 204, 242, 0.25)',
        backdropFilter: 'blur(20px)'
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.45rem',
          minWidth: 0
        }}
      >
        <span
          style={{
            fontSize: '0.72rem',
            fontWeight: 800,
            color: '#64748b',
            letterSpacing: '0.06em',
            marginRight: '0.25rem',
            textTransform: 'uppercase'
          }}
        >
          TARGET REGION:
        </span>

        {FILTERS.map((f) => {
          const isActive = activeFilter === f.id;

          return (
            <button
              key={f.id}
              type="button"
              onClick={() => onSelectFilter(f.id)}
              className={`loc-filter-pill ${isActive ? 'is-active' : ''}`}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
                padding: '0.35rem 0.75rem',
                borderRadius: '999px',
                fontSize: '0.78rem',
                fontWeight: isActive ? 700 : 500,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                border: isActive
                  ? '1.5px solid #38bdf8'
                  : '1px solid rgba(255, 255, 255, 0.12)',
                background: isActive
                  ? 'linear-gradient(135deg, rgba(56, 189, 248, 0.25), rgba(14, 165, 233, 0.15))'
                  : 'rgba(255, 255, 255, 0.04)',
                color: isActive ? '#ffffff' : '#cbd5e1',
                boxShadow: isActive
                  ? '0 0 14px rgba(56, 189, 248, 0.3)'
                  : 'none'
              }}
              title={f.sublabel ? `${f.label} (${f.sublabel})` : f.label}
              aria-pressed={isActive}
            >
              <span>{f.label}</span>
              <span
                style={{
                  fontSize: '0.7rem',
                  padding: '0.1rem 0.4rem',
                  borderRadius: '999px',
                  background: isActive ? 'rgba(0,0,0,0.35)' : 'rgba(255,255,255,0.08)',
                  color: isActive ? '#38bdf8' : '#94a3b8',
                  fontWeight: 700
                }}
              >
                {f.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Quick Action: Live Real-Time Web Scrape */}
      {onScrapePune && (
        <button
          type="button"
          onClick={onScrapePune}
          disabled={isRunning}
          className="btn-live-realtime-scrape"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.4rem 0.85rem',
            borderRadius: '10px',
            fontSize: '0.75rem',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #38bdf8, #0284c7)',
            color: '#ffffff',
            border: 'none',
            cursor: isRunning ? 'wait' : 'pointer',
            boxShadow: '0 0 16px rgba(56, 189, 248, 0.35)',
            whiteSpace: 'nowrap'
          }}
          title="Dispatch real-time web scrapers across LinkedIn, Greenhouse, Lever, Ashby, Jobicy & Remotive"
        >
          <Zap size={14} />
          <span>{isRunning ? 'Scraping Live...' : '⚡ Live Web Scrape'}</span>
        </button>
      )}
    </div>
  );
}
