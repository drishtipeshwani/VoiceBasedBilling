const MONTH_INDEX: Record<string, number> = {
  january: 1,
  jan: 1,
  february: 2,
  feb: 2,
  march: 3,
  mar: 3,
  april: 4,
  apr: 4,
  may: 5,
  june: 6,
  jun: 6,
  july: 7,
  jul: 7,
  august: 8,
  aug: 8,
  september: 9,
  sept: 9,
  sep: 9,
  october: 10,
  oct: 10,
  november: 11,
  nov: 11,
  december: 12,
  dec: 12,
};

function pad2(value: number): string {
  return String(value).padStart(2, '0');
}

export function formatDayMonthYear(day: number, month: number, year: number): string {
  return `${pad2(day)}/${pad2(month)}/${year}`;
}

function expandTwoDigitYear(year: number, now: Date): number {
  if (year >= 100) {
    return year;
  }
  const century = Math.floor(now.getFullYear() / 100) * 100;
  return century + year;
}

/**
 * Turn a spoken invoice date into DD/MM/YYYY.
 * "14th" uses the current month. A missing year uses the current year.
 */
export function resolveInvoiceDate(
  spoken: string,
  now: Date = new Date(),
): string | null {
  const text = spoken.trim().toLowerCase();
  if (!text) {
    return null;
  }

  const today = now.getDate();
  const monthNow = now.getMonth() + 1;
  const yearNow = now.getFullYear();

  if (text === 'today') {
    return formatDayMonthYear(today, monthNow, yearNow);
  }
  if (text === 'yesterday') {
    const previous = new Date(now);
    previous.setDate(today - 1);
    return formatDayMonthYear(
      previous.getDate(),
      previous.getMonth() + 1,
      previous.getFullYear(),
    );
  }
  if (text === 'tomorrow') {
    const next = new Date(now);
    next.setDate(today + 1);
    return formatDayMonthYear(next.getDate(), next.getMonth() + 1, next.getFullYear());
  }

  const dayMatch = text.match(/\b(\d{1,2})(?:st|nd|rd|th)?\b/);
  if (!dayMatch) {
    return null;
  }
  const day = Number(dayMatch[1]);
  if (!Number.isInteger(day) || day < 1 || day > 31) {
    return null;
  }

  let month = monthNow;
  const monthMatch = text.match(
    /\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\b/,
  );
  if (monthMatch) {
    month = MONTH_INDEX[monthMatch[1]];
  }

  let year = yearNow;
  const afterDay = text.slice((dayMatch.index ?? 0) + dayMatch[0].length);
  const yearMatch = afterDay.match(/\b(\d{4}|\d{2})\b/);
  if (yearMatch) {
    year = expandTwoDigitYear(Number(yearMatch[1]), now);
  }

  const resolved = new Date(year, month - 1, day);
  if (
    resolved.getFullYear() !== year ||
    resolved.getMonth() !== month - 1 ||
    resolved.getDate() !== day
  ) {
    return null;
  }

  return formatDayMonthYear(day, month, year);
}

/** Convert DD/MM/YYYY to an ISO timestamp for SQLite. */
export function invoiceDateToIso(displayDate: string | null, fallback = new Date()): string {
  if (!displayDate) {
    return fallback.toISOString();
  }
  const match = displayDate.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!match) {
    return fallback.toISOString();
  }
  const [, day, month, year] = match;
  return `${year}-${month}-${day}T00:00:00.000Z`;
}

/** Convert a stored ISO timestamp back to DD/MM/YYYY. */
export function isoToInvoiceDate(iso: string): string | null {
  const match = iso.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) {
    return null;
  }
  const [, year, month, day] = match;
  return `${day}/${month}/${year}`;
}
