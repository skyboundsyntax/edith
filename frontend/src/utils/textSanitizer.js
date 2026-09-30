/**
 * Robust Text & Description Sanitizer for Web Scraped Content.
 * Decodes HTML entities, strips all HTML tags, removes crawler watermarks,
 * and produces clean, readable typography for executive presentation.
 */

export function sanitizeJobDescription(rawText) {
  if (rawText === null || rawText === undefined) return '';
  if (typeof rawText !== 'string') {
    if (typeof rawText === 'number') return String(rawText);
    return '';
  }

  let text = rawText;

  // 1. Strip ASCII & Unicode control characters, null bytes, and directional override characters that can spoof UI
  text = text
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F\u200B-\u200D\uFEFF]/g, '')
    .replace(/[\u202A-\u202E\u2066-\u2069]/g, ''); // strip bidi overrides

  // 2. Strip dangerous script/style/iframe tags and their contents before generic tag stripping
  text = text
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, ' ')
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, ' ')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, ' ');

  // 3. Multi-pass entity decoding & HTML tag stripping
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

    // Strip any HTML tags
    text = text.replace(/<[^>]*>/gi, ' ');
  }

  // 4. Remove crawler promotions and portal watermarks
  text = text
    .replace(/Find\s+Jobs\s+in\s+[^.]*\s+on\s+Arbeitnow/gi, '')
    .replace(/Find\s+Jobs\s+in\s+Switzerland/gi, '')
    .replace(/Find\s+Jobs\s+in\s+Germany/gi, '')
    .replace(/Apply\s+(now\s+)?on\s+Arbeitnow/gi, '')
    .replace(/on\s+Arbeitnow\s*$/gi, '')
    .replace(/See\s+more\s+jobs\s+at\s+[^.]+/gi, '');

  // 5. Clean remaining stray brackets or fragments and collapse whitespace
  text = text
    .replace(/^[>\s]+/, '')
    .replace(/\s+/g, ' ')
    .trim();

  return text;
}

const TECH_ACRONYMS = {
  ai: 'AI',
  ml: 'ML',
  llm: 'LLM',
  nlp: 'NLP',
  api: 'API',
  aws: 'AWS',
  gcp: 'GCP',
  sql: 'SQL',
  nosql: 'NoSQL',
  sdk: 'SDK',
  ui: 'UI',
  ux: 'UX',
  etl: 'ETL',
  rest: 'REST',
  graphql: 'GraphQL',
  iot: 'IoT',
  devops: 'DevOps',
  cicd: 'CI/CD',
  'ci/cd': 'CI/CD'
};

export function formatSkillName(skill) {
  if (!skill) return '';
  const trimmed = String(skill).trim();
  const lower = trimmed.toLowerCase();
  if (TECH_ACRONYMS[lower]) {
    return TECH_ACRONYMS[lower];
  }
  // Replace standalone words: e.g. "Ai" -> "AI", "Ai Engineer" -> "AI Engineer"
  return trimmed
    .replace(/\bAi\b/g, 'AI')
    .replace(/\bai\b/g, 'AI')
    .replace(/\bMl\b/g, 'ML')
    .replace(/\bml\b/g, 'ML')
    .replace(/\bLlm\b/g, 'LLM')
    .replace(/\bllm\b/g, 'LLM');
}
