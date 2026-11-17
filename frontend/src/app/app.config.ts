import { registerLocaleData } from '@angular/common';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import localePl from '@angular/common/locales/pl';
import { ApplicationConfig, LOCALE_ID, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { providePrimeNG } from 'primeng/config';
import { API_INTERCEPTORS } from './api-interceptors';
import { routes } from './app.routes';
import { PRIMENG_PL } from './config/primeng-pl';
import { PlanrPreset } from './config/theme';

registerLocaleData(localePl);

export const appConfig: ApplicationConfig = {
    providers: [
        provideBrowserGlobalErrorListeners(),
        provideRouter(routes),
        provideHttpClient(withFetch(), withInterceptors(API_INTERCEPTORS)),
        { provide: LOCALE_ID, useValue: 'pl' },
        providePrimeNG({
            theme: { preset: PlanrPreset, options: { darkModeSelector: false } },
            translation: PRIMENG_PL,
        }),
    ],
};
