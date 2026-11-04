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
});
