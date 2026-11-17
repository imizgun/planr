import { addDays, fromIsoDate, isSameDay, startOfWeek, toIsoDate } from './week';

describe('startOfWeek', () => {
    it('finds the Monday of the week', () => {
        // Wednesday 11 November 2026.
        expect(startOfWeek(new Date(2026, 10, 11, 15, 30))).toEqual(new Date(2026, 10, 9));
    });

    it('treats Sunday as the last day of the week', () => {
        expect(startOfWeek(new Date(2026, 10, 15))).toEqual(new Date(2026, 10, 9));
    });

    it('keeps a Monday where it is, at midnight', () => {
        expect(startOfWeek(new Date(2026, 10, 9, 23, 59))).toEqual(new Date(2026, 10, 9));
    });
});

describe('addDays', () => {
    it('crosses months and years', () => {
        expect(addDays(new Date(2026, 11, 28), 7)).toEqual(new Date(2027, 0, 4));
        expect(addDays(new Date(2027, 0, 4), -7)).toEqual(new Date(2026, 11, 28));
    });
});

describe('toIsoDate', () => {
    it('writes the local date, not the UTC one', () => {
        expect(toIsoDate(new Date(2026, 10, 9, 0, 30))).toBe('2026-11-09');
        expect(toIsoDate(new Date(2026, 0, 1, 23, 30))).toBe('2026-01-01');
    });
});

describe('fromIsoDate', () => {
    it('reads a date back', () => {
        expect(fromIsoDate('2026-11-09')).toEqual(new Date(2026, 10, 9));
    });

    it('rejects anything that is not a real date', () => {
        expect(fromIsoDate(null)).toBeNull();
        expect(fromIsoDate('')).toBeNull();
        expect(fromIsoDate('2026-11-9')).toBeNull();
        expect(fromIsoDate('2026-02-31')).toBeNull();
        expect(fromIsoDate('next week')).toBeNull();
    });
});

describe('isSameDay', () => {
    it('ignores the time of day', () => {
        expect(isSameDay(new Date(2026, 10, 9, 1), new Date(2026, 10, 9, 23))).toBe(true);
        expect(isSameDay(new Date(2026, 10, 9), new Date(2026, 10, 10))).toBe(false);
    });
});
