import { DatePipe, NgTemplateOutlet } from '@angular/common';
import { Component, computed, DestroyRef, inject, input, signal } from '@angular/core';
import { ScheduleItem, ViewMode, WEEKDAY_LABELS, Weekday, WORK_WEEK } from '../../models/schedule';
import { SubjectCard } from '../subject-card/subject-card';
import { hourRange, placeDayItems } from './week-layout';
import { ActiveDay, dateOfDay, resolveActiveDay, stepDay, swipeStep } from './week-navigation';

const NOW_REFRESH_MS = 30_000;

/** Keep in sync with the media queries in the component styles. */
const PHONE_MEDIA_QUERY = '(max-width: 768px)';

/** Height of the current-time label, in minutes of the timeline. */
const NOW_LABEL_MINUTES = 15;

/** Card position inside its day, in percent of the day's timeline. */
interface Slot {
    item: ScheduleItem;
    top: number;
    height: number;
    left: number;
    width: number;
}

interface DayColumn {
    weekday: Weekday;
    label: string;
    slots: Slot[];
}

@Component({
    imports: [DatePipe, NgTemplateOutlet, SubjectCard],
    selector: 'app-study-week',
    styleUrl: './study-week.scss',
    templateUrl: './study-week.html',
})
export class StudyWeek {
    readonly items = input.required<ScheduleItem[]>();
    readonly viewMode = input<ViewMode>('plain');

    protected readonly now = signal(new Date());

    private readonly today = computed(() => (this.now().getDay() || 7) as Weekday);

    private readonly nowMinutes = computed(
        () => this.now().getHours() * 60 + this.now().getMinutes(),
    );

    private readonly range = computed(() => hourRange(this.items()));

    /** Full hours labelled on the timeline, including both ends of the range. */
    protected readonly hours = computed(() => {
        const { startHour, endHour } = this.range();
        const nowMinutes = this.nowMinutes();
        return Array.from({ length: endHour - startHour + 1 }, (_, i) => ({
            label: `${String(startHour + i).padStart(2, '0')}:00`,
            top: this.percentOfDay((startHour + i) * 60),
            coveredByNow: Math.abs((startHour + i) * 60 - nowMinutes) < NOW_LABEL_MINUTES,
        }));
    });

    /** Position of the current time on the timeline, or null when it is out of range. */
    protected readonly nowTop = computed(() => {
        const top = this.percentOfDay(this.nowMinutes());
        return top >= 0 && top <= 100 ? top : null;
    });

    protected readonly days = computed<DayColumn[]>(() => {
        const byDay = new Map<Weekday, ScheduleItem[]>();
        for (const item of this.items()) {
            const day = item.effective.weekday;
            byDay.set(day, [...(byDay.get(day) ?? []), item]);
        }
        // Weekend columns appear only when something is actually scheduled there.
        const weekdays = [...WORK_WEEK, ...([6, 7] as Weekday[]).filter((d) => byDay.has(d))];
        return weekdays.map((weekday) => ({
            weekday,
            label: WEEKDAY_LABELS[weekday],
            slots: placeDayItems(byDay.get(weekday) ?? []).map((placed) => ({
                item: placed.item,
                top: this.percentOfDay(placed.start),
                height: this.percentOfDay(placed.end) - this.percentOfDay(placed.start),
                left: (placed.column / placed.columns) * 100,
                width: 100 / placed.columns,
            })),
        }));
    });

    /** Day chosen by swiping; null follows the current day. */
    private readonly selectedDay = signal<ActiveDay | null>(null);

    /** The only column displayed on narrow screens. */
    protected readonly activeDay = computed(() =>
        resolveActiveDay(this.visibleWeekdays(), this.selectedDay(), this.today()),
    );

    protected readonly activeDate = computed(() => dateOfDay(this.now(), this.activeDay()));

    /** Today's column, unless swiping has moved the view to another week. */
    protected readonly highlightedDay = computed(() =>
        this.activeDay().weekOffset === 0 ? this.today() : null,
    );

    private readonly visibleWeekdays = computed(() => this.days().map((day) => day.weekday));

    private swipeStart: { x: number; y: number } | null = null;

    constructor() {
        const timer = setInterval(() => this.now.set(new Date()), NOW_REFRESH_MS);
        inject(DestroyRef).onDestroy(() => clearInterval(timer));
    }

    protected onPointerDown(event: PointerEvent) {
        if (event.isPrimary) this.swipeStart = { x: event.clientX, y: event.clientY };
    }

    protected onPointerUp(event: PointerEvent) {
        if (!event.isPrimary || !this.swipeStart) return;
        const step = swipeStep(
            event.clientX - this.swipeStart.x,
            event.clientY - this.swipeStart.y,
        );
        this.swipeStart = null;
        if (step && matchMedia(PHONE_MEDIA_QUERY).matches) {
            this.selectedDay.set(stepDay(this.visibleWeekdays(), this.activeDay(), step));
        }
    }

    /** Fired when the browser takes the gesture over, e.g. to scroll vertically. */
    protected onPointerCancel() {
        this.swipeStart = null;
    }

    private percentOfDay(minutes: number): number {
        const { startHour, endHour } = this.range();
        return ((minutes - startHour * 60) / ((endHour - startHour) * 60)) * 100;
    }
}
