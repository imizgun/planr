import { Weekday } from '../../models/schedule';

const SWIPE_MIN_DISTANCE = 50;
/** How much more horizontal than vertical a gesture must be to count as a swipe. */
const SWIPE_MIN_RATIO = 1.5;

/** A concrete day: the weekday and its distance from the current week, in weeks. */
export interface ActiveDay {
    weekday: Weekday;
    weekOffset: number;
}

/** Day step for a finished gesture: left goes to the previous day, right to the next one. */
export function swipeStep(dx: number, dy: number): -1 | 0 | 1 {
    if (Math.abs(dx) < SWIPE_MIN_DISTANCE || Math.abs(dx) < Math.abs(dy) * SWIPE_MIN_RATIO) {
        return 0;
    }
    return dx < 0 ? -1 : 1;
}

/**
 * The day shown on narrow screens: the user's choice if that column still exists, otherwise
 * today, otherwise the next visible day (a weekend without classes shows the coming Monday).
 */
export function resolveActiveDay(
    weekdays: Weekday[],
    selected: ActiveDay | null,
    today: Weekday,
): ActiveDay {
    if (selected !== null && weekdays.includes(selected.weekday)) return selected;
    const weekday = weekdays.find((day) => day >= today);
    return weekday ? { weekday, weekOffset: 0 } : { weekday: weekdays[0], weekOffset: 1 };
}

/** Neighbouring day; stepping past either end of the week continues in the adjacent week. */
export function stepDay(weekdays: Weekday[], current: ActiveDay, step: number): ActiveDay {
    const target = weekdays.indexOf(current.weekday) + step;
    return {
        weekday: weekdays[(target + weekdays.length) % weekdays.length],
        weekOffset: current.weekOffset + Math.floor(target / weekdays.length),
    };
}

export function dateOfDay(now: Date, { weekday, weekOffset }: ActiveDay): Date {
    const daysAway = weekday - (now.getDay() || 7) + weekOffset * 7;
    return new Date(now.getFullYear(), now.getMonth(), now.getDate() + daysAway);
}
