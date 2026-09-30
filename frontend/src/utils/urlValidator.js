/**
 * Production-Hardened URL & Input Validation Utility
 * Defends against:
 * - Malicious URI schemes (javascript:, data:, vbscript:, file:)
 * - XSS injection via external links
 * - Broken or malformed URLs from web crawlers
 * - Unbounded text lengths breaking UI layout
 * - Surrogate pair truncation (emojis, CJK characters)
 */

const ALLOWED_PROTOCOLS = new Set(['http:', 'https:']);

/**
 * Checks if a string is a valid, safe HTTP or HTTPS URL.
 */
export function isValidHttpUrl(string) {
  if (!string || typeof string !== 'string') return false;
  const trimmed = string.trim();
  if (!trimmed || trimmed === '#' || trimmed.startsWith('about:')) return false;

  // Guard against javascript: and data: pseudo-protocols
  const lower = trimmed.toLowerCase();
  if (
    lower.startsWith('javascript:') ||
    lower.startsWith('data:') ||
    lower.startsWith('vbscript:') ||
    lower.startsWith('file:')
  ) {
    return false;
  }

  try {
    const url = new URL(trimmed);
    return ALLOWED_PROTOCOLS.has(url.protocol);
  } catch {
    return false;
  }
}

/**
 * Returns a guaranteed safe external URL for <a href="...">.
 * If rawUrl is unsafe or empty, returns a safe search fallback URL.
 */
export function getSafeExternalUrl(rawUrl, fallbackQuery = 'verified job opening') {
  if (isValidHttpUrl(rawUrl)) {
    // Sanitize any dangerous quotes or script tags
    const sanitized = String(rawUrl).trim().replace(/[<>"'`\\]/g, '');
    return sanitized;
  }

  // Construct a safe, encoded search query
  const safeQuery = String(fallbackQuery || 'verified job opening')
    .replace(/[<>"'`]/g, ' ')
    .trim()
    .slice(0, 150);

  return `https://www.google.com/search?q=${encodeURIComponent(safeQuery)}`;
}

let graphemeSegmenter = null;
try {
  if (typeof Intl !== 'undefined' && Intl.Segmenter) {
    graphemeSegmenter = new Intl.Segmenter(undefined, { granularity: 'grapheme' });
  }
} catch {
  graphemeSegmenter = null;
}

/**
 * Truncates text safely without breaking Unicode grapheme clusters (e.g. combined emojis,
 * accents, CJK, RTL characters) or splitting words awkwardly when possible.
 */
export function truncateSafe(text, maxLength = 100, suffix = '...') {
  if (text === null || text === undefined) return '';
  const str = String(text).trim();
  if (str.length <= maxLength) return str;

  // Split by grapheme clusters if Intl.Segmenter is supported
  const graphemes = graphemeSegmenter
    ? Array.from(graphemeSegmenter.segment(str)).map((s) => s.segment)
    : Array.from(str);

  if (graphemes.length <= maxLength) return str;

  const targetLength = Math.max(0, maxLength - suffix.length);
  const sliced = graphemes.slice(0, targetLength).join('');

  // Prefer breaking at the last whitespace if within the last 25% of max length
  const lastSpaceIdx = sliced.lastIndexOf(' ');
  if (lastSpaceIdx > targetLength * 0.75) {
    return sliced.slice(0, lastSpaceIdx).trim() + suffix;
  }

  return sliced.trim() + suffix;
}

/**
 * Sanitizes search input to prevent runaway string operations or UI glitches.
 */
export function sanitizeSearchQuery(query, maxLength = 120) {
  if (!query || typeof query !== 'string') return '';
  return query
    .replace(/[\u0000-\u001F\u007F-\u009F]/g, '') // remove ASCII control characters
    .replace(/\s+/g, ' ') // collapse multiple spaces
    .trim()
    .slice(0, maxLength);
}

/**
 * Checks if a string contains RTL (Right-to-Left) characters (Arabic, Hebrew, Urdu, etc.)
 */
export function isRtlText(text) {
  if (!text || typeof text !== 'string') return false;
  // Unicode range for Hebrew, Arabic, Syriac, Thaana, Samaritan, Mandaic, etc.
  const rtlRegex = /[\u0591-\u07FF\uFB1D-\uFDFD\uFE70-\uFEFC]/;
  return rtlRegex.test(text);
}
