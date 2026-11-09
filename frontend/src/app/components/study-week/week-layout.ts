import { ScheduleItem } from '../../models/schedule';

/** Hours always visible on the timeline; items outside of them widen the range. */
const DEFAULT_START_HOUR = 8;
const DEFAULT_END_HOUR = 20;

/** Very short or malformed items still need enough height to be noticeable. */
const MIN_DURATION = 30;

export interface PlacedItem {
    item: ScheduleItem;
    /** Minutes since midnight. */
    start: number;
    end: number;
    /** Zero-based position among the items it shares the time with. */
    column: number;
    columns: number;
}

export interface HourRange {
    startHour: number;
    endHour: number;
}

export function toMinutes(time: string): number {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
}

export function hourRange(items: ScheduleItem[]): HourRange {
    const starts = items.map((i) => toMinutes(i.effective.start_time));
    const ends = items.map((i) => toMinutes(i.effective.end_time));
    return {
        startHour: Math.floor(Math.min(DEFAULT_START_HOUR * 60, ...starts) / 60),
        endHour: Math.ceil(Math.max(DEFAULT_END_HOUR * 60, ...ends) / 60),
    };
}

/**
 * Assigns side-by-side columns to one day's items. Items that overlap, directly or through
 * another item, form a cluster and split the day's width equally between its columns.
 */
export function placeDayItems(items: ScheduleItem[]): PlacedItem[] {
    const placed = items
        .map((item): PlacedItem => {
            const start = toMinutes(item.effective.start_time);
            const end = Math.max(toMinutes(item.effective.end_time), start + MIN_DURATION);
            return { item, start, end, column: 0, columns: 1 };
        })
        .sort((a, b) => a.start - b.start || b.end - a.end);

    let cluster: PlacedItem[] = [];
    let clusterEnd = -Infinity;
    for (const current of placed) {
        if (current.start >= clusterEnd) {
            assignColumns(cluster);
            cluster = [];
            clusterEnd = -Infinity;
        }
        cluster.push(current);
        clusterEnd = Math.max(clusterEnd, current.end);
    }
    assignColumns(cluster);

    return placed;
}

function assignColumns(cluster: PlacedItem[]): void {
    const columnEnds: number[] = [];
    for (const current of cluster) {
        const free = columnEnds.findIndex((end) => end <= current.start);
        current.column = free === -1 ? columnEnds.length : free;
        columnEnds[current.column] = current.end;
    }
    for (const current of cluster) {
        current.columns = columnEnds.length;
    }
}
