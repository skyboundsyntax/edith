/**
 * Robust Text & Description Sanitizer for Web Scraped Content.
 * Decodes HTML entities, strips all HTML tags, removes crawler watermarks,
 * and produces clean, readable typography for executive presentation.
 */

export function sanitizeJobDescription(rawText) {
  if (!rawText || typeof rawText !== 'string') return '';

  let text = rawText;

  // Pass 1 & 2: Decode HTML entities and strip HTML tags
  for (let pass = 0; pass < 3; pass++) {
    text = text
      .replace(/&amp;/gi, '&')
      .replace(/&lt;/gi, '<')
      .replace(/&gt;/gi, '>')
      .replace(/&quot;/gi, '"')
      .replace(/&#39;/gi, "'")
      .replace(/&#x27;/gi, "'")
      .replace(/&#x2F;/gi, '/')
      .replace(/&nbsp;/gi, ' ')
      .replace(/&ndash;/gi, '–')
      .replace(/&mdash;/gi, '—');

    // Strip any HTML tags (e.g. <p>, <em>, <strong>, <span...>, <ul>, <li>, <a...>)
    text = text.replace(/<[^>]*>/gi, ' ');
  }

  // Remove crawler promotions and portal watermarks
  text = text
    .replace(/Find\s+Jobs\s+in\s+[^.]*\s+on\s+Arbeitnow/gi, '')
    .replace(/Find\s+Jobs\s+in\s+Switzerland/gi, '')
    .replace(/Find\s+Jobs\s+in\s+Germany/gi, '')
    .replace(/Apply\s+(now\s+)?on\s+Arbeitnow/gi, '')
    .replace(/on\s+Arbeitnow\s*$/gi, '')
    .replace(/See\s+more\s+jobs\s+at\s+[^.]+/gi, '');

  // Clean remaining stray brackets or fragments
  text = text
    .replace(/^[>\s]+/, '') // remove leading '>' or whitespace
    .replace(/\s+/g, ' ')
    .trim();

  return text;
}
