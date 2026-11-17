import { Weekday } from '../../models/schedule';

const SWIPE_MIN_DISTANCE = 50;
/** How much more horizontal than vertical a gesture must be to count as a swipe. */
const SWIPE_MIN_RATIO = 1.5;

/** Where a step lands: a weekday, and the week it belongs to relative to the current one. */
export interface DayStep {
    weekday: Weekday;
    weeks: -1 | 0 | 1;
}

/**
 * Day step for a finished gesture. The day follows the finger, as a sheet of paper would:
 * dragging left pulls the next day in, dragging right brings the previous one back.
 */
export function swipeStep(dx: number, dy: number): -1 | 0 | 1 {
    if (Math.abs(dx) < SWIPE_MIN_DISTANCE || Math.abs(dx) < Math.abs(dy) * SWIPE_MIN_RATIO) {
        return 0;
    }
    return dx < 0 ? 1 : -1;
}

/**
 * The day shown on narrow screens: the user's choice if that column still exists, otherwise
 * today when the week on screen is the current one, otherwise the first day of the week.
 */
export function resolveActiveDay(
    weekdays: Weekday[],
    selected: Weekday | null,
    today: Weekday | null,
): Weekday {
    if (selected !== null && weekdays.includes(selected)) return selected;
    if (today !== null) {
        const weekday = weekdays.find((day) => day >= today);
        if (weekday) return weekday;
    }
    return weekdays[0];
}

/** Neighbouring day; stepping past either end of the week continues in the adjacent week. */
export function stepDay(weekdays: Weekday[], current: Weekday, step: -1 | 1): DayStep {
    const target = weekdays.indexOf(current) + step;
    if (target < 0) return { weekday: weekdays[weekdays.length - 1], weeks: -1 };
    if (target >= weekdays.length) return { weekday: weekdays[0], weeks: 1 };
    return { weekday: weekdays[target], weeks: 0 };
}
