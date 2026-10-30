import { DatePipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { Tag } from 'primeng/tag';
import { Tooltip } from 'primeng/tooltip';
import { ScheduleItem, ViewMode } from '../../models/schedule';

type Severity = 'info' | 'success' | 'warn' | 'secondary' | 'contrast';

const TYPE_SEVERITY: Record<string, Severity> = {
    wykład: 'info',
    laboratorium: 'success',
    ćwiczenia: 'warn',
    konwersatorium: 'contrast',
};

@Component({
    imports: [DatePipe, Tag, Tooltip],
    selector: 'app-subject-card',
    styleUrl: './subject-card.scss',
    templateUrl: './subject-card.html',
    host: { '[attr.data-type]': 'item().type' },
})
export class SubjectCard {
    readonly item = input.required<ScheduleItem>();
    readonly viewMode = input<ViewMode>('plain');

    protected readonly typeSeverity = computed<Severity>(
        () => TYPE_SEVERITY[this.item().type ?? ''] ?? 'secondary',
    );

    protected readonly timePatched = computed(() =>
        this.item().patched_fields.some((f) => f === 'start_time' || f === 'end_time'),
    );

    protected readonly isRemote = computed(() => this.item().effective.mode === 'remote');

    protected readonly teachers = computed(() =>
        this.item()
            .teachers.map((t) => t.name)
            .join(', '),
    );
}
