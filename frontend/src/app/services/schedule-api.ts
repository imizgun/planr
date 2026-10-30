import { HttpParams, httpResource } from '@angular/common/http';
import { Injectable, Signal } from '@angular/core';
import { CatalogResponse, ScheduleResponse } from '../models/schedule';

const API = '/api/v1';

export interface ScheduleQuery {
    program: string;
    groups: string[];
}

@Injectable({ providedIn: 'root' })
export class ScheduleApi {
    catalog() {
        return httpResource<CatalogResponse>(() => `${API}/catalog`);
    }

    /** Re-fetches whenever the query changes; idle while the query is undefined. */
    schedule(query: Signal<ScheduleQuery | undefined>) {
        return httpResource<ScheduleResponse>(() => {
            const q = query();
            if (!q) return undefined;
            let params = new HttpParams().set('program', q.program);
            for (const group of q.groups) params = params.append('group', group);
            return { url: `${API}/schedule`, params };
        });
    }
}
