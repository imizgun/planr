import { ScheduleItem } from '../../models/schedule';
import { hourRange, placeDayItems } from './week-layout';

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
        expect(placed.end - placed.start).toBe(30);
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
