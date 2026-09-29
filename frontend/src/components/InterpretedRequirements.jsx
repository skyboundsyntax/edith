import React, { useState } from 'react';
import { Sliders, Sparkles, MapPin, Briefcase, Code, CheckCircle, ChevronDown, ChevronUp, X, Plus } from 'lucide-react';

export default function InterpretedRequirements({
  spec,
  onUpdateSpec,
  onLaunch,
  isRunning
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [newSkill, setNewSkill] = useState('');
  const [newLocation, setNewLocation] = useState('');

  if (!spec) return null;

  const handleAddSkill = (e) => {
    e.preventDefault();
    if (!newSkill.trim()) return;
    const updated = [...(spec.skills || []), newSkill.trim()];
    onUpdateSpec({ ...spec, skills: updated });
    setNewSkill('');
  };

  const handleRemoveSkill = (skillToRemove) => {
    const updated = (spec.skills || []).filter((s) => s !== skillToRemove);
    onUpdateSpec({ ...spec, skills: updated });
  };

  const handleAddLocation = (e) => {
    e.preventDefault();
    if (!newLocation.trim()) return;
    const updated = [...(spec.locations || []), newLocation.trim()];
    onUpdateSpec({ ...spec, locations: updated });
    setNewLocation('');
  };

  const handleRemoveLocation = (locToRemove) => {
    const updated = (spec.locations || []).filter((l) => l !== locToRemove);
    onUpdateSpec({ ...spec, locations: updated });
  };

  return (
    <div className="glass-panel" style={{ marginTop: '1rem', padding: '1.25rem', border: '1px solid var(--border-amber)', borderRadius: '12px', background: 'var(--bg-secondary)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Sparkles size={18} color="var(--accent-amber)" />
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc', margin: 0 }}>
            AI Interpreted Search Specification
          </h3>
          <span style={{ fontSize: '0.72rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--text-amber)', padding: '0.15rem 0.5rem', borderRadius: '4px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
            Zero-Hallucination Query Plan
          </span>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
          onClick={() => setIsEditing(!isEditing)}
        >
          <Sliders size={13} style={{ marginRight: '0.35rem' }} />
          <span>{isEditing ? 'Collapse Editor' : 'Edit Requirements'}</span>
          {isEditing ? <ChevronUp size={13} style={{ marginLeft: '0.25rem' }} /> : <ChevronDown size={13} style={{ marginLeft: '0.25rem' }} />}
        </button>
      </div>

      {/* Summary Chips Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem' }}>
        {/* Roles */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.65rem 0.85rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Briefcase size={12} /> Target Role(s)
          </div>
          <div style={{ fontSize: '0.85rem', color: '#ffffff', fontWeight: 500 }}>
            {spec.roles && spec.roles.length > 0 ? spec.roles.join(', ') : 'Any Software / Tech Role'}
          </div>
        </div>

        {/* Locations & Remote */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.65rem 0.85rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <MapPin size={12} /> Locations & Remote
          </div>
          <div style={{ fontSize: '0.85rem', color: '#ffffff', fontWeight: 500 }}>
            {spec.locations && spec.locations.length > 0 ? spec.locations.join(', ') : 'India (Pan-India)'}
            {spec.remote && <span style={{ color: 'var(--text-amber)', marginLeft: '0.35rem' }}>(Remote Preferred)</span>}
          </div>
        </div>

        {/* Experience */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.65rem 0.85rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.35rem' }}>
            Experience Range
          </div>
          <div style={{ fontSize: '0.85rem', color: '#ffffff', fontWeight: 500 }}>
            {spec.experience_min !== null || spec.experience_max !== null
              ? `${spec.experience_min ?? 0} – ${spec.experience_max ?? 2} years`
              : 'Flexible / Entry Level'}
          </div>
        </div>

        {/* Salary Min */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.65rem 0.85rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.35rem' }}>
            Minimum Salary (CTC)
          </div>
          <div style={{ fontSize: '0.85rem', color: '#ffffff', fontWeight: 500 }}>
            {spec.salary_min ? `₹${(spec.salary_min / 100000).toFixed(1)} LPA` : 'Undisclosed / Market standard'}
          </div>
        </div>
      </div>

      {/* Skills Pill Row */}
      <div style={{ marginTop: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <Code size={12} /> Required Skills:
        </span>
        {spec.skills && spec.skills.length > 0 ? (
          spec.skills.map((skill, idx) => (
            <span
              key={idx}
              className="skill-chip"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', background: 'oklch(76% 0.17 60 / 0.14)', border: '1px solid oklch(76% 0.17 60 / 0.28)', color: 'var(--text-amber)' }}
            >
              {skill}
              {isEditing && (
                <X
                  size={11}
                  style={{ cursor: 'pointer', opacity: 0.8 }}
                  onClick={() => handleRemoveSkill(skill)}
                />
              )}
            </span>
          ))
        ) : (
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>General technical profile</span>
        )}
      </div>

      {/* Expanded Interactive Editor Panel */}
      {isEditing && (
        <div style={{ marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <h4 style={{ fontSize: '0.82rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.75rem' }}>
            Customize Search Specification
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
            {/* Add Skill */}
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Add Skill</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  placeholder="e.g. Docker, PyTorch"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  style={{ flex: 1, padding: '0.4rem 0.75rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff', fontSize: '0.8rem' }}
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleAddSkill}
                  style={{ padding: '0.4rem 0.65rem' }}
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>

            {/* Add Location */}
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Add Location</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  placeholder="e.g. Pune, Hyderabad"
                  value={newLocation}
                  onChange={(e) => setNewLocation(e.target.value)}
                  style={{ flex: 1, padding: '0.4rem 0.75rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff', fontSize: '0.8rem' }}
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleAddLocation}
                  style={{ padding: '0.4rem 0.65rem' }}
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>

            {/* Remote Preference Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginTop: '1.25rem' }}>
              <input
                type="checkbox"
                id="remoteCheck"
                checked={spec.remote}
                onChange={(e) => onUpdateSpec({ ...spec, remote: e.target.checked })}
                style={{ width: '16px', height: '16px', accentColor: 'var(--accent-amber)' }}
              />
              <label htmlFor="remoteCheck" style={{ fontSize: '0.82rem', color: '#e2e8f0', cursor: 'pointer' }}>
                Include Remote / Work From Home positions
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Action Row */}
      <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onLaunch}
          disabled={isRunning}
          style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }}
        >
          <CheckCircle size={15} style={{ marginRight: '0.4rem' }} />
          <span>{isRunning ? 'Ingestion in Progress...' : 'Confirm & Launch Real-Time Ingestion'}</span>
        </button>
      </div>
    </div>
  );
}
