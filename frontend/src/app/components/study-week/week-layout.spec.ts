import { ScheduleItem } from '../../models/schedule';
import { cardDensity, hourRange, placeDayItems, slotGeometry } from './week-layout';

function lesson(id: string, start_time: string, end_time: string): ScheduleItem {
    return { id, effective: { start_time, end_time } } as ScheduleItem;
}

function columnsById(items: ScheduleItem[]) {
    return Object.fromEntries(placeDayItems(items).map((p) => [p.item.id, [p.column, p.columns]]));
}

describe('placeDayItems', () => {
    it('gives the full width to items that do not overlap', () => {
        expect(columnsById([lesson('a', '08:00', '09:30'), lesson('b', '10:00', '11:30')])).toEqual(
            {
                a: [0, 1],
                b: [0, 1],
            },
        );
    });

    it('treats back-to-back items as not overlapping', () => {
        expect(columnsById([lesson('a', '08:00', '09:30'), lesson('b', '09:30', '11:00')])).toEqual(
            {
                a: [0, 1],
                b: [0, 1],
            },
        );
    });

    it('puts simultaneous items side by side', () => {
        expect(columnsById([lesson('a', '08:00', '09:30'), lesson('b', '08:00', '09:30')])).toEqual(
            {
                a: [0, 2],
                b: [1, 2],
            },
        );
    });

    it('reuses a freed column within a chain of overlaps', () => {
        expect(
            columnsById([
                lesson('a', '08:00', '09:30'),
                lesson('b', '09:00', '10:30'),
                lesson('c', '10:00', '11:30'),
            ]),
        ).toEqual({ a: [0, 2], b: [1, 2], c: [0, 2] });
    });

    it('sizes clusters independently', () => {
        expect(
            columnsById([
                lesson('a', '08:00', '09:30'),
                lesson('b', '08:00', '09:30'),
                lesson('c', '12:00', '13:30'),
            ]),
        ).toEqual({ a: [0, 2], b: [1, 2], c: [0, 1] });
    });

    it('keeps a minimum height for items with a malformed end time', () => {
        const [placed] = placeDayItems([lesson('a', '08:00', '08:00')]);
        expect(placed.end - placed.start).toBe(40);
    });
});

describe('hourRange', () => {
    it('falls back to the default hours', () => {
        expect(hourRange([])).toEqual({ startHour: 8, endHour: 20 });
    });

    it('widens to whole hours around outlying items', () => {
        expect(hourRange([lesson('a', '07:30', '20:15')])).toEqual({ startHour: 7, endHour: 21 });
    });
});

describe('slotGeometry', () => {
    it('gives a lone item the whole day', () => {
        expect(slotGeometry(0, 1)).toEqual({ left: 0, width: 100, staggered: false });
    });

    it('splits the width between two items', () => {
        expect(slotGeometry(0, 2)).toEqual({ left: 0, width: 50, staggered: false });
        expect(slotGeometry(1, 2)).toEqual({ left: 50, width: 50, staggered: false });
    });

    it('staggers three or more items instead of narrowing them further', () => {
        expect(slotGeometry(0, 3)).toEqual({ left: 0, width: 60, staggered: true });
        expect(slotGeometry(1, 3)).toEqual({ left: 20, width: 60, staggered: true });
        expect(slotGeometry(2, 3)).toEqual({ left: 40, width: 60, staggered: true });
    });

    it('keeps the last staggered card inside the day', () => {
        const last = slotGeometry(3, 4);
        expect(last.left + last.width).toBe(100);
    });
});

describe('cardDensity', () => {
    it('keeps the name and the time in the shortest slots', () => {
        expect(cardDensity(40, false)).toBe('xs');
        expect(cardDensity(45, false)).toBe('xs');
    });

    it('adds the room, then the type, as the slot gets longer', () => {
        expect(cardDensity(60, false)).toBe('sm');
        expect(cardDensity(75, false)).toBe('md');
        expect(cardDensity(90, false)).toBe('lg');
    });

    it('shows everything once a slot is long enough for the teacher', () => {
        expect(cardDensity(120, false)).toBe('full');
        expect(cardDensity(180, false)).toBe('full');
    });

    it('leaves the teacher out of a narrow column whatever its length', () => {
        expect(cardDensity(180, true)).toBe('lg');
    });
});
