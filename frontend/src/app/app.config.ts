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

/** PrimeUI community license key (client-side, ships in the bundle by design). */
const PRIMEUI_LICENSE =
    'eyJpZCI6IjBlNzJhY2UwLWUzNWYtNGJiNi04NWQ1LTliNGJhYmYxOTc4MSIsInByb2R1Y3QiOiJwcmltZXVpIiwidGllciI6ImNvbW11bml0eSIsInR5cGUiOiJkZXYiLCJpYXQiOjE3OTUxODIxNjgsImV4cCI6MTgyNjcxODE2OH0.jJSX7CECVGoliM0JcR3-KhxyPzDb7iRieRo5x-TQGP5UtbnIu5LNXKTcyMV75CTvKHe3u2EQSd1HbOaq-heBBQ';

export const appConfig: ApplicationConfig = {
    providers: [
        provideBrowserGlobalErrorListeners(),
        provideRouter(routes),
        provideHttpClient(withFetch(), withInterceptors(API_INTERCEPTORS)),
        { provide: LOCALE_ID, useValue: 'pl' },
        providePrimeNG({
            theme: { preset: PlanrPreset, options: { darkModeSelector: false } },
            translation: PRIMENG_PL,
            license: PRIMEUI_LICENSE,
        }),
    ],
};
