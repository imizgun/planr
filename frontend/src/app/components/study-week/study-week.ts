import { Component, computed, input } from '@angular/core';
import { ScheduleItem, ViewMode, WEEKDAY_LABELS, Weekday, WORK_WEEK } from '../../models/schedule';
import { SubjectCard } from '../subject-card/subject-card';

interface DayColumn {
    weekday: Weekday;
    label: string;
    items: ScheduleItem[];
}

@Component({
    imports: [SubjectCard],
    selector: 'app-study-week',
    styleUrl: './study-week.scss',
    templateUrl: './study-week.html',
})
export class StudyWeek {
    readonly items = input.required<ScheduleItem[]>();
    readonly viewMode = input<ViewMode>('plain');

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
            items: (byDay.get(weekday) ?? []).sort((a, b) =>
                a.effective.start_time.localeCompare(b.effective.start_time),
            ),
        }));
    });
}
