import React, { useState, useEffect } from 'react';
import { X, User, Briefcase, MapPin, DollarSign, Code, Save, CheckCircle2, GraduationCap, Globe } from 'lucide-react';
import { api } from '../services/api';

export default function CandidateProfileModal({ isOpen, onClose, onProfileUpdated }) {
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    skills: [],
    experience_years: 0.0,
    education: '',
    preferred_roles: [],
    preferred_locations: [],
    remote_preference: true,
    salary_expectation: 600000.0,
    github_url: '',
    linkedin_url: '',
    portfolio_url: ''
  });

  const [skillsInput, setSkillsInput] = useState('');
  const [rolesInput, setRolesInput] = useState('');
  const [locationsInput, setLocationsInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      api.getUserProfile().then((data) => {
        if (data.exists && data.profile) {
          setProfile(data.profile);
          setSkillsInput((data.profile.skills || []).join(', '));
          setRolesInput((data.profile.preferred_roles || []).join(', '));
          setLocationsInput((data.profile.preferred_locations || []).join(', '));
        }
      }).catch((err) => console.error('Failed to load profile:', err));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSavedSuccess(false);

    const updatedProfile = {
      ...profile,
      skills: skillsInput.split(',').map((s) => s.trim()).filter(Boolean),
      preferred_roles: rolesInput.split(',').map((r) => r.trim()).filter(Boolean),
      preferred_locations: locationsInput.split(',').map((l) => l.trim()).filter(Boolean),
      experience_years: Number(profile.experience_years) || 0,
      salary_expectation: Number(profile.salary_expectation) || 0
    };

    try {
      await api.saveUserProfile(updatedProfile);
      setSavedSuccess(true);
      if (onProfileUpdated) onProfileUpdated(updatedProfile);
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 1000);
    } catch (err) {
      alert(`Failed to save profile: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-container" style={{ maxWidth: '680px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <User size={20} color="var(--accent-cyan)" />
            <div>
              <h2 style={{ fontSize: '1.15rem', margin: 0, fontWeight: 600 }}>Job Seeker Candidate Profile</h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Enable personalized Profile-to-Job match scoring
              </span>
            </div>
          </div>
          <button className="btn-icon" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ maxHeight: '68vh', overflowY: 'auto' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>Full Name</label>
                <input
                  type="text"
                  className="input-field"
                  value={profile.name || ''}
                  onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                  placeholder="e.g. Rahul Sharma"
                  style={{ width: '100%', padding: '0.55rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>Education Qualification</label>
                <input
                  type="text"
                  className="input-field"
                  value={profile.education || ''}
                  onChange={(e) => setProfile({ ...profile, education: e.target.value })}
                  placeholder="e.g. B.Tech Computer Science (2025)"
                  style={{ width: '100%', padding: '0.55rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
                Skills & Tech Stack (comma separated)
              </label>
              <input
                type="text"
                className="input-field"
                value={skillsInput}
                onChange={(e) => setSkillsInput(e.target.value)}
                placeholder="e.g. Python, React, FastAPI, SQL, Machine Learning, Docker"
                style={{ width: '100%', padding: '0.55rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>Experience (in years)</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="15"
                  className="input-field"
                  value={profile.experience_years}
                  onChange={(e) => setProfile({ ...profile, experience_years: e.target.value })}
                  style={{ width: '100%', padding: '0.55rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>Expected Annual Salary (₹ INR)</label>
                <input
                  type="number"
                  step="50000"
                  min="0"
                  className="input-field"
                  value={profile.salary_expectation}
                  onChange={(e) => setProfile({ ...profile, salary_expectation: e.target.value })}
                  placeholder="e.g. 800000 for ₹8 LPA"
                  style={{ width: '100%', padding: '0.55rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>Preferred Roles</label>
                <input
                  type="text"
                  className="input-field"
                  value={rolesInput}
                  onChange={(e) => setRolesInput(e.target.value)}
                  placeholder="e.g. Python Developer, AI Engineer Intern"
                  style={{ width: '100%', padding: '0.55rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>Preferred Locations</label>
                <input
                  type="text"
                  className="input-field"
                  value={locationsInput}
                  onChange={(e) => setLocationsInput(e.target.value)}
                  placeholder="e.g. Pune, Bangalore, Remote"
                  style={{ width: '100%', padding: '0.55rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff' }}
                />
              </div>
            </div>

            {/* Remote Preference */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1rem' }}>
              <input
                type="checkbox"
                id="profRemote"
                checked={profile.remote_preference}
                onChange={(e) => setProfile({ ...profile, remote_preference: e.target.checked })}
                style={{ width: '16px', height: '16px', accentColor: 'var(--accent-cyan)' }}
              />
              <label htmlFor="profRemote" style={{ fontSize: '0.82rem', color: '#e2e8f0', cursor: 'pointer' }}>
                Open to Remote / Work-From-Home Opportunities
              </label>
            </div>
          </div>

          <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose} style={{ fontSize: '0.85rem' }}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving} style={{ fontSize: '0.85rem' }}>
              {savedSuccess ? (
                <>
                  <CheckCircle2 size={15} style={{ marginRight: '0.35rem' }} />
                  <span>Saved!</span>
                </>
              ) : (
                <>
                  <Save size={15} style={{ marginRight: '0.35rem' }} />
                  <span>{saving ? 'Saving...' : 'Save Profile'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
