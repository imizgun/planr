import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ScheduleItem } from '../../models/schedule';
import { startOfWeek } from '../../models/week';
import { StudyWeek } from './study-week';

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

describe('StudyWeek', () => {
    let component: StudyWeek;
    let fixture: ComponentFixture<StudyWeek>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [StudyWeek],
        }).compileComponents();

        fixture = TestBed.createComponent(StudyWeek);
        fixture.componentRef.setInput('items', [ITEM]);
        // Monday of the week the test's item belongs to.
        fixture.componentRef.setInput('weekStart', startOfWeek(new Date()));
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('opens the details of a clicked card', async () => {
        fixture.nativeElement.querySelector('.slot').click();
        await fixture.whenStable();

        const card = document.querySelector('.p-dialog app-subject-card');
        expect(card?.getAttribute('data-density')).toBe('detail');
        expect(card?.textContent).toContain('Analiza matematyczna');
    });

    it('offers a way back once the view moves to another day', async () => {
        expect(fixture.nativeElement.querySelector('.today-jump')).toBeNull();

        fixture.nativeElement.querySelector('.day-title .day-nav button').click();
        await fixture.whenStable();

        const back = fixture.nativeElement.querySelector('.today-jump button');
        expect(back).not.toBeNull();

        back.click();
        await fixture.whenStable();
        expect(fixture.nativeElement.querySelector('.today-jump')).toBeNull();
    });

    it('shortens a card that does not fit its slot', async () => {
        const short = { ...ITEM, effective: { ...ITEM.effective, end_time: '08:45' } };
        fixture.componentRef.setInput('items', [short]);
        await fixture.whenStable();

        const card = fixture.nativeElement.querySelector('app-subject-card');
        expect(card.getAttribute('data-density')).toBe('xs');
    });
});
