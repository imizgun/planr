import { computed, effect, inject, Injectable, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, ParamMap, Params, Router } from '@angular/router';
import { ViewMode } from '../models/schedule';
import { addDays, fromIsoDate, startOfWeek, toIsoDate } from '../models/week';

const STORAGE_KEY = 'planr.settings';

interface StoredSettings {
    programId: string | null;
    groupIds: string[];
    /** `<courseId>:<groupId>`, or a bare `<courseId>` for electives without groups. */
    electives: string[];
    viewMode: ViewMode;
}

const DEFAULTS: StoredSettings = {
    programId: null,
    groupIds: [],
    electives: [],
    viewMode: 'plain',
};

function load(): StoredSettings {
    try {
        return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}') };
    } catch {
        return DEFAULTS;
    }
}

function save(settings: StoredSettings) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch {
        // Storage may be unavailable (private mode); the selection then lasts for the session.
    }
}

/**
 * What the plan on screen is made of. Everything the schedule request is built from lives in
 * the query string, so that a plan can be shared, bookmarked and reloaded as a link; the last
 * selection is also remembered and fills in a bare URL. The view mode is a preference rather
 * than part of the plan, so it stays in storage only.
 */
@Injectable({ providedIn: 'root' })
export class PlanSettings {
    private readonly route = inject(ActivatedRoute);
    private readonly router = inject(Router);

    private readonly params = toSignal(this.route.queryParamMap, {
        initialValue: this.route.snapshot.queryParamMap,
    });

    readonly programId = computed(() => this.params().get('program'));
    readonly groupIds = computed(() => this.params().getAll('group'));
    /** `<courseId>:<groupId>`, or a bare `<courseId>` for electives without groups. */
    readonly electives = computed(() => this.params().getAll('elective'));

    /** Monday of the week on screen; the schedule is asked for that week alone. */
    readonly weekStart = computed(() =>
        startOfWeek(fromIsoDate(this.params().get('from')) ?? new Date()),
    );

    readonly weekEnd = computed(() => addDays(this.weekStart(), 6));

    private readonly stored = load();

    readonly viewMode = signal<ViewMode>(this.stored.viewMode);

    constructor() {
        effect(() => this.remember(this.params(), this.viewMode()));
        this.restore();
    }

    selectProgram(id: string | null) {
        if (id === this.programId()) return;
        // Groups and electives belong to a programme, so they do not survive the change.
        this.update({ program: id, group: null, elective: null });
    }

    setGroups(ids: string[]) {
        this.update({ group: ids });
    }

    setElectives(values: string[]) {
        this.update({ elective: values });
    }

    /** Moves the window by whole weeks. */
    stepWeek(weeks: number) {
        this.showWeekOf(addDays(this.weekStart(), weeks * 7));
    }

    showCurrentWeek() {
        this.showWeekOf(new Date());
    }

    private showWeekOf(date: Date) {
        const start = startOfWeek(date);
        this.update({ from: toIsoDate(start), to: toIsoDate(addDays(start, 6)) });
    }

    /** Fills a URL that carries no plan with the last one, so that it keeps working as a link. */
    private restore() {
        const params = this.params();
        const patch: Params = {};
        if (!params.get('program') && this.stored.programId) {
            patch['program'] = this.stored.programId;
            patch['group'] = this.stored.groupIds;
            patch['elective'] = this.stored.electives;
        }
        if (!fromIsoDate(params.get('from')) || !fromIsoDate(params.get('to'))) {
            const start = this.weekStart();
            patch['from'] = toIsoDate(start);
            patch['to'] = toIsoDate(addDays(start, 6));
        }
        if (Object.keys(patch).length) this.update(patch);
    }

    /** Keeps the last plan, and the view mode, for the next visit. */
    private remember(params: ParamMap, viewMode: ViewMode) {
        save({
            programId: params.get('program') ?? this.stored.programId,
            groupIds: params.get('program') ? params.getAll('group') : this.stored.groupIds,
            electives: params.get('program') ? params.getAll('elective') : this.stored.electives,
            viewMode,
        });
    }

    private update(params: Params) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: params,
            queryParamsHandling: 'merge',
            // The address bar holds the plan, not a trail of every filter the user tried.
            replaceUrl: true,
        });
    }
}
