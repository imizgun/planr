import { Routes } from '@angular/router';
import { PlanPage } from './pages/plan-page/plan-page';

export const routes: Routes = [
    { path: '', component: PlanPage },
    { path: '**', redirectTo: '' },
];
