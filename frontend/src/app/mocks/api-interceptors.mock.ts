import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { of } from 'rxjs';
import { MOCK_CATALOG, MOCK_SCHEDULE } from './mock-schedule';

const mockApi: HttpInterceptorFn = (req, next) => {
    const path = new URL(req.url, location.origin).pathname;
    if (path === '/api/v1/catalog') return of(new HttpResponse({ body: MOCK_CATALOG }));
    if (path === '/api/v1/schedule') return of(new HttpResponse({ body: MOCK_SCHEDULE }));
    return next(req);
};

/** Replaces `app/api-interceptors.ts` in the `mock` build configuration. */
export const API_INTERCEPTORS: HttpInterceptorFn[] = [mockApi];
