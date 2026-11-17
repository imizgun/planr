/**
 * Calendar maths for the week on screen. Everything works on local dates: the schedule is
 * a local calendar, and `toISOString()` would move a date across the time zone.
 */

/** Monday of the week the given day belongs to, at midnight. */
export function startOfWeek(date: Date): Date {
    return addDays(date, 1 - (date.getDay() || 7));
}

export function addDays(date: Date, days: number): Date {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
}

export function isSameDay(a: Date, b: Date): boolean {
    return (
        a.getFullYear() === b.getFullYear() &&
        a.getMonth() === b.getMonth() &&
        a.getDate() === b.getDate()
    );
}

/** The date as the API spells it, YYYY-MM-DD. */
export function toIsoDate(date: Date): string {
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${date.getFullYear()}-${month}-${day}`;
}

/** Reads YYYY-MM-DD as a local date; null for anything else, a 31st of February included. */
export function fromIsoDate(value: string | null | undefined): Date | null {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value ?? '');
    if (!match) return null;
    const [year, month, day] = match.slice(1).map(Number);
    const date = new Date(year, month - 1, day);
    return date.getMonth() === month - 1 && date.getDate() === day ? date : null;
}
