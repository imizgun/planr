import { Weekday } from '../../models/schedule';
import { resolveActiveDay, stepDay, swipeStep } from './week-navigation';

const WORK_WEEK: Weekday[] = [1, 2, 3, 4, 5];

describe('swipeStep', () => {
    it('goes to the next day on a swipe left', () => {
        expect(swipeStep(-120, 5)).toBe(1);
    });

    it('goes to the previous day on a swipe right', () => {
        expect(swipeStep(120, 5)).toBe(-1);
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
        expect(resolveActiveDay(WORK_WEEK, null, 3)).toBe(3);
    });

    it('prefers the selected day', () => {
        expect(resolveActiveDay(WORK_WEEK, 5, 3)).toBe(5);
    });

    it('forgets a selected day that is no longer displayed', () => {
        expect(resolveActiveDay(WORK_WEEK, 6, 3)).toBe(3);
    });

    it('opens another week on its first day', () => {
        expect(resolveActiveDay(WORK_WEEK, null, null)).toBe(1);
    });

    it('shows the coming Monday on a weekend without classes', () => {
        expect(resolveActiveDay(WORK_WEEK, null, 7)).toBe(1);
    });

    it('shows a weekend day when it has its own column', () => {
        expect(resolveActiveDay([...WORK_WEEK, 6], null, 6)).toBe(6);
    });
});

describe('stepDay', () => {
    it('moves within the week', () => {
        expect(stepDay(WORK_WEEK, 2, 1)).toEqual({ weekday: 3, weeks: 0 });
        expect(stepDay(WORK_WEEK, 2, -1)).toEqual({ weekday: 1, weeks: 0 });
    });

    it('continues in the adjacent week past the ends of the week', () => {
        expect(stepDay(WORK_WEEK, 5, 1)).toEqual({ weekday: 1, weeks: 1 });
        expect(stepDay(WORK_WEEK, 1, -1)).toEqual({ weekday: 5, weeks: -1 });
    });
});
