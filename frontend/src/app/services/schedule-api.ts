import { HttpParams, httpResource } from '@angular/common/http';
import { Injectable, Signal } from '@angular/core';
import { CatalogResponse, ScheduleResponse } from '../models/schedule';

const API = '/api/v1';

export interface ScheduleQuery {
    program: string;
    groups: string[];
    /** `<courseId>:<groupId>`, or a bare `<courseId>` for electives without groups. */
    electives: string[];
    /** Window of the plan, as YYYY-MM-DD; classes outside it are left out of the answer. */
    from: string;
    to: string;
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
            let params = new HttpParams()
                .set('program', q.program)
                .set('from', q.from)
                .set('to', q.to);
            for (const group of q.groups) params = params.append('group', group);
            for (const elective of q.electives) params = params.append('elective', elective);
            return { url: `${API}/schedule`, params };
        });
    }
}
