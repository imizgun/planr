import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ScheduleItem } from '../../models/schedule';
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
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
