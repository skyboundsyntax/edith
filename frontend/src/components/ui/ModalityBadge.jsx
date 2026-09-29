import React from 'react';
import { Globe, Building2, Shuffle } from 'lucide-react';

/**
 * Reusable Modality Badge component extracted from Job Dossier and List Cards.
 * Resilient against null, undefined, mixed-case, and internationalized inputs.
 */
export default function ModalityBadge({
  modality = 'offline',
  remoteType = '',
  rawLocation = '',
  size = 'md',
  showIcon = true,
  className = ''
}) {
  const modLower = String(modality || '').toLowerCase();
  const remLower = String(remoteType || '').toLowerCase();
  const locLower = String(rawLocation || '').toLowerCase();

  const isOnline =
    modLower === 'online' ||
    remLower === 'remote' ||
    /remote|online|virtual|wfh|telecommute/i.test(locLower);

  const isHybrid =
    modLower === 'hybrid' ||
    remLower === 'hybrid' ||
    /hybrid/i.test(locLower);

  const typeClass = isOnline ? 'online' : isHybrid ? 'hybrid' : 'offline';
  const label = isOnline
    ? 'ONLINE // REMOTE'
    : isHybrid
      ? 'HYBRID // FLEXIBLE'
      : 'OFFLINE // ON-SITE';

  const iconSize = size === 'sm' ? 12 : size === 'lg' ? 16 : 14;

  return (
    <span
      className={`dossier-modality-flag ${typeClass} size-${size} ${className}`}
      dir="auto"
      role="status"
      aria-label={`Work modality: ${label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        minWidth: 0,
        maxWidth: '100%',
        whiteSpace: 'nowrap'
      }}
    >
      {showIcon && (
        <span style={{ display: 'inline-flex', flexShrink: 0 }}>
          {isOnline ? (
            <Globe size={iconSize} aria-hidden="true" />
          ) : isHybrid ? (
            <Shuffle size={iconSize} aria-hidden="true" />
          ) : (
            <Building2 size={iconSize} aria-hidden="true" />
          )}
        </span>
      )}
      <span
        style={{
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}
      >
        {label}
      </span>
    </span>
  );
}
