import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Message } from 'primeng/message';
import { MultiSelect } from 'primeng/multiselect';
import { ProgressSpinner } from 'primeng/progressspinner';
import { Select } from 'primeng/select';
import { SelectButton } from 'primeng/selectbutton';
import { StudyWeek } from '../../components/study-week/study-week';
import { ViewMode } from '../../models/schedule';
import { PlanSettings } from '../../services/plan-settings';
import { ScheduleApi, ScheduleQuery } from '../../services/schedule-api';

@Component({
    imports: [
        DatePipe,
        FormsModule,
        Message,
        MultiSelect,
        ProgressSpinner,
        Select,
        SelectButton,
        StudyWeek,
    ],
    selector: 'app-plan-page',
    styleUrl: './plan-page.scss',
    templateUrl: './plan-page.html',
})
export class PlanPage {
    private readonly api = inject(ScheduleApi);
    protected readonly settings = inject(PlanSettings);

    protected readonly viewModes: { label: string; value: ViewMode }[] = [
        { label: 'Oryginalny', value: 'plain' },
        { label: 'Z uwagami', value: 'annotated' },
    ];

    protected readonly catalog = this.api.catalog();

    protected readonly programs = computed(() => this.catalog.value()?.programs ?? []);

    protected readonly program = computed(() =>
        this.programs().find((p) => p.id === this.settings.programId()),
    );

    /** Stored group ids that still exist in the current catalog. */
    protected readonly groupIds = computed(() => {
        const known = new Set(this.program()?.groups.map((g) => g.id));
        return this.settings.groupIds().filter((id) => known.has(id));
    });

    private readonly query = computed<ScheduleQuery | undefined>(() => {
        const program = this.program();
        return program ? { program: program.id, groups: this.groupIds() } : undefined;
    });

    protected readonly schedule = this.api.schedule(this.query);

    protected errorText(error: unknown): string {
        if (error instanceof HttpErrorResponse) {
            if (error.status === 503) return 'Backend nie ma jeszcze danych planu.';
            if (error.status === 0) return 'Brak połączenia z serwerem.';
            return error.error?.detail ?? error.message;
        }
        return String(error);
    }
}
