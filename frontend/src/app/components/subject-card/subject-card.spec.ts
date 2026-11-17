import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ScheduleItem } from '../../models/schedule';
import { SubjectCard } from './subject-card';

const ITEM: ScheduleItem = {
    id: 'slot_1',
    course: { id: 'crs_1', name: 'Analiza matematyczna' },
    type: 'wykład',
    group: { id: null, label: null, program_wide: true },
    teachers: [{ id: 't_1', name: 'dr Jan Kowalski' }],
    room: '1.23',
    block: { weekday: 1, start_hour: 8, count: 2 },
    effective: {
        weekday: 1,
        start_time: '08:00',
        end_time: '09:30',
        mode: 'stationary',
        date_from: null,
        date_to: null,
    },
    patched_fields: [],
    remark: { raw: null, parse_status: 'ok', unparsed: null, needs_review: false },
    proposals: [],
};

describe('SubjectCard', () => {
    let component: SubjectCard;
    let fixture: ComponentFixture<SubjectCard>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [SubjectCard],
        }).compileComponents();

        fixture = TestBed.createComponent(SubjectCard);
        fixture.componentRef.setInput('item', ITEM);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('keeps the time, the name, the type and the room in a shortened card', async () => {
        fixture.componentRef.setInput('density', 'lg');
        await fixture.whenStable();

        const card: HTMLElement = fixture.nativeElement;
        expect(card.querySelector('.time')?.textContent).toBe('08:00–09:30');
        expect(card.querySelector('.course')?.textContent).toContain('Analiza matematyczna');
        expect(card.querySelector('.tags')?.textContent).toContain('wykład');
        expect(card.querySelector('.details')?.textContent).toContain('1.23');
        // The teacher is still rendered, and only hidden by the styles until the card unfolds.
        expect(card.querySelector('.teacher')).not.toBeNull();
    });

    /** Lets the card measure itself against a slot of the given height. */
    function withSlot(height: number, content: Record<string, number>) {
        const card: HTMLElement = fixture.nativeElement;
        Object.defineProperty(card, 'clientHeight', { configurable: true, get: () => height });
        Object.defineProperty(card, 'scrollHeight', {
            configurable: true,
            get: () => content[card.dataset['density'] ?? ''] ?? 0,
        });
        return card;
    }

    it('shows more than its slot suggested when the card has room to spare', async () => {
        const card = withSlot(120, { xs: 50, sm: 70, md: 90, lg: 110, full: 130 });

        fixture.componentRef.setInput('density', 'sm');
        await fixture.whenStable();

        expect(card.dataset['density']).toBe('lg');
    });

    it('drops rows until the card fits its slot', async () => {
        const card = withSlot(120, { xs: 50, sm: 70, md: 110, lg: 150, full: 200 });

        fixture.componentRef.setInput('density', 'lg');
        await fixture.whenStable();

        expect(card.dataset['density']).toBe('md');
    });

    it('spells the date range out in the dialog only', async () => {
        const limited = {
            ...ITEM,
            effective: { ...ITEM.effective, date_from: '2026-11-05', date_to: '2026-12-17' },
        };
        fixture.componentRef.setInput('item', limited);
        await fixture.whenStable();

        const card: HTMLElement = fixture.nativeElement;
        expect(card.querySelector('.details')?.textContent).not.toContain('od 5.11');
        expect(card.querySelector('.date-range-icon')).not.toBeNull();

        fixture.componentRef.setInput('density', 'detail');
        await fixture.whenStable();
        expect(card.querySelector('.details')?.textContent).toContain('od 5.11 do 17.12');
        expect(card.querySelector('.date-range-icon')).toBeNull();
    });
});
