/**
 * Currency Formatter Utility for EDITH
 * Standardizes all compensation figures into Indian Rupees (₹) and LPA (Lakhs Per Annum).
 */

const USD_TO_INR = 86; // standard conversion
const EUR_TO_INR = 92;
const GBP_TO_INR = 110;

const inrFormatter = new Intl.NumberFormat('en-IN', {
  maximumFractionDigits: 0
});

/**
 * Formats Indian number system with commas: 1850000 -> 18,50,000
 * Handles negative, zero, extreme values, and non-number inputs defensively.
 */
export function formatIndianCurrency(amount) {
  if (amount === null || amount === undefined) return '0';
  const num = typeof amount === 'number' ? amount : parseFloat(String(amount).replace(/,/g, ''));
  if (!Number.isFinite(num)) return '0';
  // Clamp to reasonable financial range to prevent integer overflow
  const clamped = Math.max(-10000000000, Math.min(10000000000, Math.round(num)));
  try {
    return inrFormatter.format(clamped);
  } catch {
    return String(clamped);
  }
}

/**
 * Parses any incoming salary text and returns equivalent annual INR value in Rupees.
 */
export function parseSalaryToInr(salaryText) {
  if (salaryText === null || salaryText === undefined) return null;
  const str = String(salaryText).trim().toLowerCase().slice(0, 150);
  if (
    !str ||
    str === 'not disclosed' ||
    str === 'undisclosed' ||
    str.includes('competitive') ||
    str.includes('disclosed on application')
  ) {
    return null;
  }

  // 1. Check for LPA / Lakhs: e.g. "8-18 LPA", "12 LPA", "₹15 Lakh", "6 lpa"
  const lpaMatch =
    str.match(/(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)/i) ||
    str.match(/(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)/i);
  if (lpaMatch) {
    const lpa = lpaMatch[2]
      ? (parseFloat(lpaMatch[1]) + parseFloat(lpaMatch[2])) / 2
      : parseFloat(lpaMatch[1]);
    return lpa * 100000;
  }

  // 2. Check for USD: e.g. "$120k-$150k", "$120,000", "120k USD"
  const usdKMatch =
    str.match(/\$?\s*(\d+(?:\.\d+)?)\s*k\s*(?:-|to)\s*\$?\s*(\d+(?:\.\d+)?)\s*k/i) ||
    str.match(/\$?\s*(\d+(?:\.\d+)?)\s*k/i);
  if (usdKMatch && (str.includes('$') || str.includes('usd') || str.includes('k'))) {
    const kVal = usdKMatch[2]
      ? (parseFloat(usdKMatch[1]) + parseFloat(usdKMatch[2])) / 2
      : parseFloat(usdKMatch[1]);
    return kVal * 1000 * USD_TO_INR;
  }

  const usdFullMatch = str.match(/\$([0-9,]+)/) || str.match(/([0-9,]+)\s*usd/i);
  if (usdFullMatch) {
    const num = parseFloat(usdFullMatch[1].replace(/,/g, ''));
    if (!isNaN(num) && num > 1000) {
      return num * USD_TO_INR;
    }
  }

  // 3. Check for EUR: e.g. "€60k", "€60,000"
  const eurMatch = str.match(/€\s*(\d+(?:\.\d+)?)\s*k/i) || str.match(/€([0-9,]+)/);
  if (eurMatch) {
    let num = parseFloat(eurMatch[1].replace(/,/g, ''));
    if (str.includes('k') && num < 1000) num *= 1000;
    return num * EUR_TO_INR;
  }

  // 4. Raw INR number: e.g. "₹6,00,000", "800000", "₹1200000"
  const rawNumMatch = str.match(/(?:₹|inr|rs\.?)\s*([0-9,]+)/i) || str.match(/([0-9,]{5,})/);
  if (rawNumMatch) {
    const num = parseFloat(rawNumMatch[1].replace(/,/g, ''));
    if (!isNaN(num) && num > 10000) {
      return num;
    }
  }

  return null;
}

/**
 * Normalizes any salary text to an elegant Indian Rupee representation.
 */
export function formatSalaryInRupees(salaryText, fallback = 'Competitive Market CTC') {
  if (
    !salaryText ||
    salaryText === 'Not Disclosed' ||
    salaryText === 'Undisclosed' ||
    salaryText === 'Market Competitive' ||
    String(salaryText).toLowerCase().includes('disclosed on application')
  ) {
    return fallback;
  }

  const str = String(salaryText).trim();

  // If already in Indian Rupee / LPA format:
  if (/lpa|lac|lakh/i.test(str)) {
    let cleaned = str.replace(/inr|rs\.?/gi, '').trim();
    if (!cleaned.startsWith('₹')) {
      cleaned = `₹${cleaned}`;
    }
    return cleaned;
  }

  // If in USD $ / k:
  const usdMatch =
    str.match(/\$?\s*(\d+(?:\.\d+)?)\s*k\s*(?:-|to)\s*\$?\s*(\d+(?:\.\d+)?)\s*k/i) ||
    str.match(/\$?\s*(\d+(?:\.\d+)?)\s*k/i);
  if (usdMatch && (str.includes('$') || str.toLowerCase().includes('usd'))) {
    if (usdMatch[2]) {
      const minLPA = ((parseFloat(usdMatch[1]) * 1000 * USD_TO_INR) / 100000).toFixed(0);
      const maxLPA = ((parseFloat(usdMatch[2]) * 1000 * USD_TO_INR) / 100000).toFixed(0);
      return `₹${minLPA} - ${maxLPA} LPA`;
    } else {
      const lpa = ((parseFloat(usdMatch[1]) * 1000 * USD_TO_INR) / 100000).toFixed(1);
      return `₹${lpa} LPA`;
    }
  }

  // If full USD amount like $120,000
  const usdFull = str.match(/\$([0-9,]+)/);
  if (usdFull) {
    const num = parseFloat(usdFull[1].replace(/,/g, ''));
    if (!isNaN(num) && num > 1000) {
      const lpa = ((num * USD_TO_INR) / 100000).toFixed(1);
      return `₹${lpa} LPA`;
    }
  }

  // If EUR:
  const eurMatch = str.match(/€([0-9,]+)/);
  if (eurMatch) {
    const num = parseFloat(eurMatch[1].replace(/,/g, ''));
    if (!isNaN(num)) {
      const lpa = ((num * EUR_TO_INR) / 100000).toFixed(1);
      return `₹${lpa} LPA`;
    }
  }

  // If raw INR amount like 1200000 or ₹12,00,000:
  const inrRaw = parseSalaryToInr(str);
  if (inrRaw) {
    const lpa = (inrRaw / 100000).toFixed(1);
    return `₹${lpa} LPA`;
  }

  // If already starts with ₹:
  if (str.startsWith('₹')) return str;

  return `₹${str}`;
}

/**
 * Computes aggregate salary intelligence in Indian Rupees.
 */
export function calculateAverageRupeeSalary(records = []) {
  const safeRecords = Array.isArray(records) ? records : [];
  let totalInr = 0;
  let count = 0;

  for (const r of safeRecords) {
    const sal = r?.data?.salary_range;
    const inrVal = parseSalaryToInr(sal);
    if (inrVal && inrVal > 0) {
      totalInr += inrVal;
      count++;
    }
  }

  // Default to typical high-demand tech CTC in India (18.5 LPA = ₹18,50,000) if no data disclosed
  const avgInr = count > 0 ? Math.round(totalInr / count) : 1850000;
  const avgLPA = (avgInr / 100000).toFixed(1);
  const formattedInr = `₹${formatIndianCurrency(avgInr)}`;
  const lpaDisplay = `₹${avgLPA} LPA`;

  // Scale progress from 5 LPA to 50 LPA
  const minScale = 500000;
  const maxScale = 5000000;
  const progressPercent = Math.min(
    95,
    Math.max(25, Math.round(((avgInr - minScale) / (maxScale - minScale)) * 100))
  );

  return {
    lpaDisplay,
    annualDisplay: `${formattedInr} / yr`,
    avgDisplay: lpaDisplay,
    subDisplay: `Average salary ${lpaDisplay}`,
    progressPercent,
    sampleCount: count
  };
}

/**
 * Extracts numeric minimum and maximum LPA values from any salary string.
 * Returns { minLpa: number | null, maxLpa: number | null, isDisclosed: boolean }
 */
export function parseSalaryRangeLPA(salaryText) {
  if (!salaryText) return { minLpa: null, maxLpa: null, isDisclosed: false };
  const str = String(salaryText).trim().toLowerCase();
  if (
    str === 'not disclosed' ||
    str === 'undisclosed' ||
    str === 'competitive market ctc' ||
    str.includes('competitive') ||
    str.includes('disclosed on application')
  ) {
    return { minLpa: null, maxLpa: null, isDisclosed: false };
  }

  // 1. Range in LPA: e.g. '30-40 LPA', '₹30 - 40 LPA', '30lpa-40lpa', '30 to 40 lac'
  const lpaRange = str.match(/(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)?\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)/i);
  if (lpaRange) {
    return {
      minLpa: parseFloat(lpaRange[1]),
      maxLpa: parseFloat(lpaRange[2]),
      isDisclosed: true
    };
  }

  // 2. Single LPA: e.g. '35 LPA', '₹35 LPA', '35lpa'
  const singleLpa = str.match(/(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)/i);
  if (singleLpa) {
    const val = parseFloat(singleLpa[1]);
    return { minLpa: val, maxLpa: val, isDisclosed: true };
  }

  // 3. USD range: e.g. '$120k-$150k' -> converted to INR LPA
  const usdRange = str.match(/\$?\s*(\d+(?:\.\d+)?)\s*k\s*(?:-|to)\s*\$?\s*(\d+(?:\.\d+)?)\s*k/i);
  if (usdRange) {
    const minVal = (parseFloat(usdRange[1]) * 1000 * USD_TO_INR) / 100000;
    const maxVal = (parseFloat(usdRange[2]) * 1000 * USD_TO_INR) / 100000;
    return { minLpa: Math.round(minVal), maxLpa: Math.round(maxVal), isDisclosed: true };
  }

  // 4. Raw INR: '₹30,00,000' -> 30 LPA
  const rawNumMatch = str.match(/(?:₹|inr|rs\.?)\s*([0-9,]+)/i) || str.match(/([0-9,]{5,})/);
  if (rawNumMatch) {
    const num = parseFloat(rawNumMatch[1].replace(/,/g, ''));
    if (!isNaN(num) && num > 10000) {
      const lpa = Math.round((num / 100000) * 10) / 10;
      return { minLpa: lpa, maxLpa: lpa, isDisclosed: true };
    }
  }

  return { minLpa: null, maxLpa: null, isDisclosed: false };
}

/**
 * Extracts salary bracket intent from search query strings (e.g. 'python 30lpa-40lpa').
 * Strips out the salary portion so keywords match role titles cleanly.
 */
export function extractSalaryQuery(queryText) {
  if (!queryText || typeof queryText !== 'string') {
    return { minLpa: null, maxLpa: null, remainingQuery: '', hasSalaryFilter: false };
  }

  let text = queryText;
  let minLpa = null;
  let maxLpa = null;
  let hasSalaryFilter = false;

  // 1. Range match: '30lpa-40lpa', '30-40 lpa', '30 to 40 LPA', '₹30 - 40 LPA', '₹30LPA - ₹40LPA'
  const rangeMatch = text.match(/(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)?\s*(?:-|to)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)/i);
  if (rangeMatch) {
    minLpa = parseFloat(rangeMatch[1]);
    maxLpa = parseFloat(rangeMatch[2]);
    hasSalaryFilter = true;
    text = text.replace(rangeMatch[0], ' ');
  } else {
    // 2. Minimum or Plus match: '30+ lpa', 'min 30 lpa', '30 lpa+'
    const plusMatch = text.match(/(?:minimum|min|at least)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)\s*\+?/i);
    if (plusMatch && (text.includes('+') || /min|at least/i.test(plusMatch[0]))) {
      minLpa = parseFloat(plusMatch[1]);
      maxLpa = null;
      hasSalaryFilter = true;
      text = text.replace(plusMatch[0], ' ');
    } else {
      // 3. Single match: '35lpa', '35 LPA', '₹35 LPA'
      const singleMatch = text.match(/(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)/i);
      if (singleMatch) {
        const val = parseFloat(singleMatch[1]);
        minLpa = val;
        maxLpa = val;
        hasSalaryFilter = true;
        text = text.replace(singleMatch[0], ' ');
      }
    }
  }

  const remainingQuery = text.replace(/\s+/g, ' ').trim();
  return { minLpa, maxLpa, remainingQuery, hasSalaryFilter };
}

/**
 * Validates if a job listing satisfies the requested salary bracket.
 * Rule:
 * - Shows jobs strictly inside / overlapping the bracket.
 * - Shows jobs with unlisted / undisclosed salaries.
 * - Discards / hides jobs with listed salaries strictly outside the bracket.
 */
export function matchesSalaryBracket(salaryText, targetMinLpa, targetMaxLpa) {
  if (
    (targetMinLpa === null || targetMinLpa === undefined) &&
    (targetMaxLpa === null || targetMaxLpa === undefined)
  ) {
    return true;
  }

  const { minLpa: jobMin, maxLpa: jobMax, isDisclosed } = parseSalaryRangeLPA(salaryText);

  // If salary is unlisted/undisclosed, always include it
  if (!isDisclosed || jobMin === null) {
    return true;
  }

  const reqMin = (targetMinLpa !== null && targetMinLpa !== undefined) ? Number(targetMinLpa) : 0;
  const reqMax = (targetMaxLpa !== null && targetMaxLpa !== undefined) ? Number(targetMaxLpa) : Infinity;

  const actualJobMin = jobMin;
  const actualJobMax = jobMax !== null ? jobMax : jobMin;

  // If job's maximum salary is strictly below requested minimum -> outside bracket
  if (actualJobMax < reqMin) {
    return false;
  }

  // If job's minimum salary is strictly above requested maximum -> outside bracket
  if (actualJobMin > reqMax) {
    return false;
  }

  return true;
}

