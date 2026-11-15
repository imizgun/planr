import { Weekday } from '../../models/schedule';
import { dateOfDay, resolveActiveDay, stepDay, swipeStep } from './week-navigation';

const WORK_WEEK: Weekday[] = [1, 2, 3, 4, 5];

describe('swipeStep', () => {
    it('goes to the previous day on a swipe left', () => {
        expect(swipeStep(-120, 5)).toBe(-1);
    });

    it('goes to the next day on a swipe right', () => {
        expect(swipeStep(120, 5)).toBe(1);
    });

    it('ignores short movements', () => {
        expect(swipeStep(30, 0)).toBe(0);
    });

    it('ignores mostly vertical movements', () => {
        expect(swipeStep(80, 100)).toBe(0);
    });
});

describe('resolveActiveDay', () => {
    it('defaults to today', () => {
        expect(resolveActiveDay(WORK_WEEK, null, 3)).toEqual({ weekday: 3, weekOffset: 0 });
    });

    it('prefers the selected day', () => {
        const selected = { weekday: 5, weekOffset: 1 } as const;
        expect(resolveActiveDay(WORK_WEEK, selected, 3)).toEqual(selected);
    });

    it('forgets a selected day that is no longer displayed', () => {
        expect(resolveActiveDay(WORK_WEEK, { weekday: 6, weekOffset: 0 }, 3)).toEqual({
            weekday: 3,
            weekOffset: 0,
        });
    });

    it('shows the coming Monday on a weekend without classes', () => {
        expect(resolveActiveDay(WORK_WEEK, null, 7)).toEqual({ weekday: 1, weekOffset: 1 });
    });

    it('shows a weekend day when it has its own column', () => {
        expect(resolveActiveDay([...WORK_WEEK, 6], null, 6)).toEqual({ weekday: 6, weekOffset: 0 });
    });
});

describe('stepDay', () => {
    it('moves within the week', () => {
        expect(stepDay(WORK_WEEK, { weekday: 2, weekOffset: 0 }, 1)).toEqual({
            weekday: 3,
            weekOffset: 0,
        });
        expect(stepDay(WORK_WEEK, { weekday: 2, weekOffset: 0 }, -1)).toEqual({
            weekday: 1,
            weekOffset: 0,
        });
    });

    it('continues in the adjacent week past the ends of the week', () => {
        expect(stepDay(WORK_WEEK, { weekday: 5, weekOffset: 0 }, 1)).toEqual({
            weekday: 1,
            weekOffset: 1,
        });
        expect(stepDay(WORK_WEEK, { weekday: 1, weekOffset: 0 }, -1)).toEqual({
            weekday: 5,
            weekOffset: -1,
        });
    });
});

describe('dateOfDay', () => {
    // Wednesday.
    const now = new Date(2026, 10, 11, 12, 30);

    it('finds a day of the current week', () => {
        expect(dateOfDay(now, { weekday: 1, weekOffset: 0 })).toEqual(new Date(2026, 10, 9));
    });

    it('applies the week offset across a month boundary', () => {
        expect(dateOfDay(now, { weekday: 1, weekOffset: 3 })).toEqual(new Date(2026, 10, 30));
        expect(dateOfDay(now, { weekday: 2, weekOffset: 3 })).toEqual(new Date(2026, 11, 1));
    });

    it('treats Sunday as the last day of the week', () => {
        const sunday = new Date(2026, 10, 15);
        expect(dateOfDay(sunday, { weekday: 1, weekOffset: 0 })).toEqual(new Date(2026, 10, 9));
    });
});
