import { DatePipe, formatDate, NgTemplateOutlet } from '@angular/common';
import {
    Component,
    computed,
    DestroyRef,
    inject,
    input,
    LOCALE_ID,
    output,
    signal,
} from '@angular/core';
import { ScheduleItem, ViewMode, WEEKDAY_LABELS, Weekday, WORK_WEEK } from '../../models/schedule';
import { addDays, isSameDay, startOfWeek } from '../../models/week';
import { Button } from 'primeng/button';
import { Dialog } from 'primeng/dialog';
import { CardDensity, SubjectCard } from '../subject-card/subject-card';
import { cardDensity, hourRange, placeDayItems, slotGeometry } from './week-layout';
import { resolveActiveDay, stepDay, swipeStep } from './week-navigation';

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
    /** Overlapping card that is only partly visible until it is hovered or opened. */
    staggered: boolean;
    column: number;
    /** How much of the card fits the slot. */
    density: CardDensity;
}

interface DayColumn {
    weekday: Weekday;
    label: string;
    date: Date;
    slots: Slot[];
}

@Component({
    imports: [Button, DatePipe, Dialog, NgTemplateOutlet, SubjectCard],
    selector: 'app-study-week',
    styleUrl: './study-week.scss',
    templateUrl: './study-week.html',
})
export class StudyWeek {
    private readonly locale = inject(LOCALE_ID);

    readonly items = input.required<ScheduleItem[]>();
    readonly viewMode = input<ViewMode>('plain');

    /** Monday of the week the items belong to. */
    readonly weekStart = input.required<Date>();

    /** Asks for a neighbouring week, which is a different request. */
    readonly weekStep = output<-1 | 1>();

    /** Asks to come back to the week, and the day, the plan opens on. */
    readonly todayRequested = output<void>();

    protected readonly now = signal(new Date());

    /** Today's weekday, or null while another week is on screen. */
    private readonly today = computed(() => {
        const now = this.now();
        return isSameDay(startOfWeek(now), this.weekStart())
            ? ((now.getDay() || 7) as Weekday)
            : null;
    });

    private readonly nowMinutes = computed(
        () => this.now().getHours() * 60 + this.now().getMinutes(),
    );

    private readonly range = computed(() => hourRange(this.items()));

    protected readonly weekLabel = computed(() => {
        const start = this.weekStart();
        const end = addDays(start, 6);
        const day = (date: Date, format: string) => formatDate(date, format, this.locale);
        return start.getMonth() === end.getMonth()
            ? `${day(start, 'd')}–${day(end, 'd MMMM y')}`
            : `${day(start, 'd MMM')} – ${day(end, 'd MMM y')}`;
    });

    /** Whether the week on screen is the one that holds today. */
    protected readonly currentWeek = computed(() => this.today() !== null);

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

    /** Position of the current time on the timeline; null outside the range or another week. */
    protected readonly nowTop = computed(() => {
        if (!this.currentWeek()) return null;
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
            date: addDays(this.weekStart(), weekday - 1),
            slots: placeDayItems(byDay.get(weekday) ?? []).map((placed) => ({
                item: placed.item,
                top: this.percentOfDay(placed.start),
                height: this.percentOfDay(placed.end) - this.percentOfDay(placed.start),
                ...slotGeometry(placed.column, placed.columns),
                column: placed.column,
                density: cardDensity(placed.end - placed.start, placed.columns > 1),
            })),
        }));
    });

    /** Day chosen by swiping or stepping; null follows today. */
    private readonly selectedDay = signal<Weekday | null>(null);

    private readonly visibleWeekdays = computed(() => this.days().map((day) => day.weekday));

    /** The only column displayed on narrow screens. */
    protected readonly activeDay = computed(() =>
        resolveActiveDay(this.visibleWeekdays(), this.selectedDay(), this.today()),
    );

    /** Whether the plan is showing something other than today. */
    protected readonly movedAway = computed(
        () => !this.currentWeek() || this.activeDay() !== this.today(),
    );

    /** Today's column, unless another week is on screen. */
    protected readonly highlightedDay = computed(() => this.today());

    /** Class whose full details are open in the dialog. */
    protected readonly openedItem = signal<ScheduleItem | null>(null);

    protected readonly openedLabel = computed(() => {
        const item = this.openedItem();
        return item ? WEEKDAY_LABELS[item.effective.weekday] : '';
    });

    protected readonly openedDate = computed(() => {
        const item = this.openedItem();
        return item ? addDays(this.weekStart(), item.effective.weekday - 1) : null;
    });

    private swipeStart: { x: number; y: number } | null = null;

    /** A swipe ends in a click on the card under the finger, which must not open it. */
    private swiped = false;

    constructor() {
        const timer = setInterval(() => this.now.set(new Date()), NOW_REFRESH_MS);
        inject(DestroyRef).onDestroy(() => clearInterval(timer));
    }

    protected onPointerDown(event: PointerEvent) {
        if (!event.isPrimary) return;
        this.swipeStart = { x: event.clientX, y: event.clientY };
        this.swiped = false;
    }

    protected onPointerUp(event: PointerEvent) {
        if (!event.isPrimary || !this.swipeStart) return;
        const step = swipeStep(
            event.clientX - this.swipeStart.x,
            event.clientY - this.swipeStart.y,
        );
        this.swipeStart = null;
        if (step && matchMedia(PHONE_MEDIA_QUERY).matches) {
            this.step(step);
            this.swiped = true;
        }
    }

    /** Moves the single-day view of narrow screens to a neighbouring day. */
    protected step(step: -1 | 1) {
        const target = stepDay(this.visibleWeekdays(), this.activeDay(), step);
        this.selectedDay.set(target.weekday);
        if (target.weeks) this.weekStep.emit(target.weeks);
    }

    /** Fired when the browser takes the gesture over, e.g. to scroll vertically. */
    protected onPointerCancel() {
        this.swipeStart = null;
    }

    protected goToToday() {
        this.selectedDay.set(null);
        this.todayRequested.emit();
    }

    protected openCard(item: ScheduleItem) {
        if (!this.swiped) this.openedItem.set(item);
    }

    protected onDialogVisibleChange(visible: boolean) {
        if (!visible) this.openedItem.set(null);
    }

    private percentOfDay(minutes: number): number {
        const { startHour, endHour } = this.range();
        return ((minutes - startHour * 60) / ((endHour - startHour) * 60)) * 100;
    }
}
