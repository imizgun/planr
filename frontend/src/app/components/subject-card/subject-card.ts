import { formatDate } from '@angular/common';
import {
    afterRenderEffect,
    Component,
    computed,
    DestroyRef,
    ElementRef,
    inject,
    input,
    linkedSignal,
    LOCALE_ID,
    untracked,
} from '@angular/core';
import { Tag } from 'primeng/tag';
import { Tooltip } from 'primeng/tooltip';
import { ScheduleItem, ViewMode } from '../../models/schedule';

type Severity = 'info' | 'success' | 'warn' | 'secondary' | 'contrast';

/**
 * How much of a card fits its slot. Every step keeps what the smaller ones keep and adds the
 * next field by importance: name and time first, then the room, the type, the teacher. What
 * a card leaves out is a hover or a tap away, in the dialog, which uses 'detail' and is the
 * only place the dates and the remarks are spelled out.
 *
 * - 'xs'   time, name on one line
 * - 'sm'   time, name on two lines
 * - 'md'   and the room
 * - 'lg'   and the type, the group and whether the class is remote
 * - 'full' and the teacher
 */
export type CardDensity = 'xs' | 'sm' | 'md' | 'lg' | 'full' | 'detail';

/** The levels a card can be shown at, from the fullest down to the barest. */
const LEVELS: CardDensity[] = ['full', 'lg', 'md', 'sm', 'xs'];

const TYPE_SEVERITY: Record<string, Severity> = {
    wykład: 'info',
    laboratorium: 'success',
    ćwiczenia: 'warn',
    konwersatorium: 'contrast',
};

@Component({
    imports: [Tag, Tooltip],
    selector: 'app-subject-card',
    styleUrl: './subject-card.scss',
    templateUrl: './subject-card.html',
    host: { '[attr.data-type]': 'item().type', '[attr.data-density]': 'shown()' },
})
export class SubjectCard {
    private readonly locale = inject(LOCALE_ID);
    private readonly host: HTMLElement = inject(ElementRef).nativeElement;

    readonly item = input.required<ScheduleItem>();
    readonly viewMode = input<ViewMode>('plain');

    /** What the slot's height suggests; how much actually fits is measured afterwards. */
    readonly density = input<CardDensity>('full');

    /** The level the card is drawn at, once it has measured itself against its slot. */
    protected readonly shown = linkedSignal(() => this.density());

    protected readonly isDetail = computed(() => this.density() === 'detail');

    constructor() {
        afterRenderEffect(() => {
            this.item();
            this.fit(this.density());
        });

        // The column's width changes with the window, and with it the lines of the name.
        if (typeof ResizeObserver !== 'undefined') {
            const observer = new ResizeObserver(() => this.fit(untracked(this.density)));
            observer.observe(this.host);
            inject(DestroyRef).onDestroy(() => observer.disconnect());
        }
    }

    /**
     * Shows as much of the card as its slot really has room for. The estimate from the slot's
     * length assumes a name of two lines, so a card with a short name has a row to spare and
     * one with a name that wraps further has one too many.
     */
    private fit(estimate: CardDensity) {
        const slot = this.host.closest('.slot');
        // An unfolded card shows everything anyway, and one without a box cannot be measured.
        if (estimate === 'detail' || !this.host.clientHeight) return;
        if (slot && (slot === document.activeElement || slot.matches(':hover'))) return;

        let level = Math.max(LEVELS.indexOf(estimate), 0);
        if (this.cutAt(level)) {
            while (level < LEVELS.length - 1 && this.cutAt(++level)) {
                // Keep dropping the least important row until the card fits.
            }
        } else {
            while (level > 0 && !this.cutAt(level - 1)) level--;
        }
        this.draw(LEVELS[level]);
        this.shown.set(LEVELS[level]);
    }

    /** Draws the card at the given level and reports whether its slot cuts it off. */
    private cutAt(level: number): boolean {
        this.draw(LEVELS[level]);
        // Both heights are whole pixels, so a line cut in half is always caught here.
        return this.host.scrollHeight > this.host.clientHeight;
    }

    private draw(level: CardDensity) {
        this.host.setAttribute('data-density', level);
    }

    /** Exact hours of the class; the timeline rail only marks full hours. */
    protected readonly time = computed(
        () => `${this.item().effective.start_time}–${this.item().effective.end_time}`,
    );

    protected readonly typeSeverity = computed<Severity>(
        () => TYPE_SEVERITY[this.item().type ?? ''] ?? 'secondary',
    );

    protected readonly timePatched = computed(() =>
        this.item().patched_fields.some((f) => f === 'start_time' || f === 'end_time'),
    );

    protected readonly isRemote = computed(() => this.item().effective.mode === 'remote');

    /** Dates limiting the class to a part of the semester, as 'od 5.11 do 17.12'. */
    protected readonly dateRange = computed(() => {
        const { date_from, date_to } = this.item().effective;
        const parts: string[] = [];
        if (date_from) parts.push(`od ${this.day(date_from)}`);
        if (date_to) parts.push(`do ${this.day(date_to)}`);
        return parts.join(' ');
    });

    protected readonly teachers = computed(() =>
        this.item()
            .teachers.map((t) => t.name)
            .join(', '),
    );

    /** The group's label, unless the class is held for the whole programme. */
    protected readonly groupLabel = computed(() => {
        const group = this.item().group;
        return group && !group.program_wide ? group.label : null;
    });

    protected readonly hasTags = computed(
        () => !!this.item().type || !!this.groupLabel() || this.isRemote(),
    );

    /** Remarks belong to the annotated view, and are always spelled out in the dialog. */
    protected readonly showAnnotations = computed(
        () => this.isDetail() || this.viewMode() === 'annotated',
    );

    private day(date: string): string {
        return formatDate(date, 'd.MM', this.locale);
    }
}
