import { effect, Injectable, signal } from '@angular/core';
import { ViewMode } from '../models/schedule';

const STORAGE_KEY = 'planr.settings';

interface StoredSettings {
    programId: string | null;
    groupIds: string[];
    viewMode: ViewMode;
}

const DEFAULTS: StoredSettings = { programId: null, groupIds: [], viewMode: 'plain' };

function load(): StoredSettings {
    try {
        return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}') };
    } catch {
        return DEFAULTS;
    }
}

/** User's schedule selection, persisted in localStorage. */
@Injectable({ providedIn: 'root' })
export class PlanSettings {
    private readonly initial = load();

    readonly programId = signal<string | null>(this.initial.programId);
    readonly groupIds = signal<string[]>(this.initial.groupIds);
    readonly viewMode = signal<ViewMode>(this.initial.viewMode);

    constructor() {
        effect(() => {
            const settings: StoredSettings = {
                programId: this.programId(),
                groupIds: this.groupIds(),
                viewMode: this.viewMode(),
            };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
        });
    }

    selectProgram(id: string | null) {
        if (id === this.programId()) return;
        this.programId.set(id);
        this.groupIds.set([]);
    }
}
