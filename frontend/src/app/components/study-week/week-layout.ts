import { CardDensity } from '../subject-card/subject-card';
import { ScheduleItem } from '../../models/schedule';

/** Hours always visible on the timeline; items outside of them widen the range. */
const DEFAULT_START_HOUR = 8;
const DEFAULT_END_HOUR = 20;

/** Very short or malformed items still need the height of a card's name and time. */
const MIN_DURATION = 40;

/** Height of an hour of the timeline, in pixels. Keep in sync with --hour-height. */
const HOUR_HEIGHT = 80;

/**
 * What a card's parts cost in height, in pixels. Keep in sync with subject-card.scss: a card
 * that does not fit its slot is cut, and the cut lands in the middle of a line of text.
 */
const CARD_FRAME = 14;
const CARD_GAP = 4;
const TIME_ROW = 15;
const NAME_LINE = 19;
const DETAILS_GAP = 2;
const DETAILS_ROW = 16;
const TAGS_ROW = 20;

/**
 * Width a card keeps, in percent of the day, once three or more items overlap: an equal split
 * would leave each one too narrow for its name.
 */
const STAGGERED_WIDTH = 60;

export interface PlacedItem {
    item: ScheduleItem;
    /** Minutes since midnight. */
    start: number;
    end: number;
    /** Zero-based position among the items it shares the time with. */
    column: number;
    columns: number;
}

/** Horizontal placement of a card, in percent of the day's width. */
export interface SlotGeometry {
    left: number;
    width: number;
    /** True when the card overlaps its neighbours instead of sharing the width with them. */
    staggered: boolean;
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

/**
 * Where a card sits across its day. Up to two items split the width between them; three or
 * more overlap in a staircase instead, so every card stays readable and shows its left edge,
 * which carries the time.
 */
export function slotGeometry(column: number, columns: number): SlotGeometry {
    if (columns <= 2) {
        return { left: (column / columns) * 100, width: 100 / columns, staggered: false };
    }
    return {
        left: (column / (columns - 1)) * (100 - STAGGERED_WIDTH),
        width: STAGGERED_WIDTH,
        staggered: true,
    };
}

/**
 * What a card in a slot of the given length, in minutes, can be expected to show. Fields are
 * given up in reverse order of importance: the teacher first, then the type, then the room,
 * and the second line of the name last; a narrow column, where the teacher's name wraps
 * worst, starts without it. This assumes a name of two lines, so it is only the card's
 * starting point: the card measures itself afterwards and corrects it either way.
 */
export function cardDensity(minutes: number, narrow: boolean): CardDensity {
    const height = (minutes / 60) * HOUR_HEIGHT;
    const name = CARD_FRAME + TIME_ROW + CARD_GAP + NAME_LINE;
    if (height < name + NAME_LINE) return 'xs';
    const withRoom = name + NAME_LINE + CARD_GAP + DETAILS_ROW;
    if (height < withRoom) return 'sm';
    const withTags = withRoom + CARD_GAP + TAGS_ROW;
    if (height < withTags) return 'md';
    const withTeacher = withTags + DETAILS_GAP + DETAILS_ROW;
    if (height < withTeacher || narrow) return 'lg';
    return 'full';
}
