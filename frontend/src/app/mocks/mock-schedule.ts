import {
    CatalogResponse,
    Effective,
    ScheduleItem,
    ScheduleResponse,
    Weekday,
} from '../models/schedule';

const SOURCE = { version: 'mock', fetched_at: '2026-11-09T08:00:00+01:00' };
const PROGRAM = { id: 'mock-program', name: 'Informatyka (dane testowe)' };
const GROUP = { id: 'grp_mock', label: 'Gr. 1', program_wide: false };
const PROGRAM_WIDE = { id: null, label: null, program_wide: true };

interface LessonDraft {
    weekday: Weekday;
    start: string;
    end: string;
    course: string;
    type?: string;
    teacher?: string;
    room?: string;
    programWide?: boolean;
    remark?: string;
    needsReview?: boolean;
    patchedFields?: string[];
    effective?: Partial<Effective>;
}

function lesson(draft: LessonDraft, index: number): ScheduleItem {
    const id = `mock_${index}`;
    return {
        id,
        course: { id: `crs_${draft.course}`, name: draft.course },
        type: draft.type ?? 'wykład',
        group: draft.programWide ? PROGRAM_WIDE : GROUP,
        teachers: draft.teacher ? [{ id: `t_${draft.teacher}`, name: draft.teacher }] : [],
        room: draft.room ?? null,
        block: { weekday: draft.weekday, start_hour: Number(draft.start.split(':')[0]), count: 2 },
        effective: {
            weekday: draft.weekday,
            start_time: draft.start,
            end_time: draft.end,
            mode: 'stationary',
            date_from: null,
            date_to: null,
            ...draft.effective,
        },
        patched_fields: draft.patchedFields ?? [],
        remark: {
            raw: draft.remark ?? null,
            parse_status: 'ok',
            unparsed: null,
            needs_review: draft.needsReview ?? false,
        },
        proposals: [],
    };
}

// prettier-ignore
const LESSONS: LessonDraft[] = [
    // Monday: regular day, with an evening lesson to exercise the current-time line.
    { weekday: 1, start: '08:00', end: '09:30', course: 'Analiza matematyczna', teacher: 'dr Jan Kowalski', room: '1.23', programWide: true },
    { weekday: 1, start: '09:45', end: '11:15', course: 'Analiza matematyczna', type: 'ćwiczenia', teacher: 'mgr Anna Nowak', room: '2.14' },
    { weekday: 1, start: '11:30', end: '14:30', course: 'Programowanie obiektowe', type: 'laboratorium', teacher: 'dr Piotr Wiśniewski', room: '4.05' },
    { weekday: 1, start: '17:00', end: '20:00', course: 'Bazy danych', type: 'laboratorium', teacher: 'mgr Ewa Zielińska', room: '4.11' },

    // Tuesday: two lessons at exactly the same time.
    { weekday: 2, start: '10:00', end: '11:30', course: 'Algebra liniowa', type: 'ćwiczenia', teacher: 'dr Maria Lewandowska', room: '3.02' },
    { weekday: 2, start: '10:00', end: '11:30', course: 'Język angielski', type: 'konwersatorium', teacher: 'mgr John Smith', room: '1.40' },
    { weekday: 2, start: '13:15', end: '14:45', course: 'Systemy operacyjne', teacher: 'prof. Adam Dąbrowski', room: 'A1', programWide: true, remark: 'Wykład co dwa tygodnie' },

    // Wednesday: a chain of partial overlaps, three columns at the widest point.
    { weekday: 3, start: '08:30', end: '11:30', course: 'Sieci komputerowe', type: 'laboratorium', teacher: 'dr Tomasz Kamiński', room: '4.07' },
    { weekday: 3, start: '09:00', end: '10:30', course: 'Fakultet: Grafika 3D', type: 'konwersatorium', teacher: 'dr Olga Wójcik', room: '2.22' },
    { weekday: 3, start: '10:00', end: '11:30', course: 'Fakultet: Kryptografia', teacher: 'dr hab. Marek Szymański', room: '1.05' },
    { weekday: 3, start: '11:00', end: '12:30', course: 'Statystyka', type: 'ćwiczenia', teacher: 'mgr Karol Woźniak', room: '3.11' },

    // Thursday: back-to-back lessons, plus remote, patched and date-limited variants.
    { weekday: 4, start: '09:00', end: '10:30', course: 'Inżynieria oprogramowania', teacher: 'dr Julia Mazur', room: 'zdalnie', programWide: true, effective: { mode: 'remote' } },
    { weekday: 4, start: '10:30', end: '12:00', course: 'Inżynieria oprogramowania', type: 'laboratorium', teacher: 'mgr Paweł Krawczyk', room: '4.03' },
    { weekday: 4, start: '12:45', end: '14:15', course: 'Metody numeryczne', type: 'ćwiczenia', teacher: 'dr Natalia Piotrowska', room: '2.08', patchedFields: ['start_time', 'end_time'], remark: 'Od 15.11 zajęcia o 12:45', needsReview: true },
    { weekday: 4, start: '15:00', end: '16:30', course: 'Seminarium dyplomowe z bardzo długą nazwą przedmiotu do sprawdzenia zawijania', type: 'konwersatorium', teacher: 'prof. Krzysztof Grabowski', room: '5.01', effective: { date_from: '2026-11-05', date_to: '2026-12-17' } },

    // Friday: a short lesson, and a type without dedicated styling.
    { weekday: 5, start: '08:00', end: '08:45', course: 'BHP', teacher: 'mgr Barbara Pawłowska', room: 'A2', programWide: true },
    { weekday: 5, start: '09:00', end: '12:00', course: 'Warsztaty zespołowe', type: 'projekt', teacher: 'dr Michał Michalski', room: '4.12' },
];

export const MOCK_CATALOG: CatalogResponse = {
    schema_version: 1,
    source: SOURCE,
    programs: [
        {
            ...PROGRAM,
            groups: [{ id: GROUP.id, label: GROUP.label }],
            electives: [],
        },
    ],
};

export const MOCK_SCHEDULE: ScheduleResponse = {
    schema_version: 1,
    program: PROGRAM,
    source: { ...SOURCE, timezone: 'Europe/Warsaw' },
    items: LESSONS.map(lesson),
};
