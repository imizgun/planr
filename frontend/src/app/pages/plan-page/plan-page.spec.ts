import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { NavigationEnd, provideRouter, Router } from '@angular/router';
import { filter, firstValueFrom } from 'rxjs';
import { PlanPage } from './plan-page';

const CATALOG = {
    schema_version: 1,
    source: { version: 'v1', fetched_at: '' },
    programs: [
        {
            id: 'prg_1',
            name: 'Informatyka',
            groups: [{ id: 'grp_2', label: 'gr. 2' }],
            electives: [
                { id: 'crs_3', name: 'Grafika 3D', groups: [{ id: 'grp_7', label: 'gr. 1' }] },
            ],
        },
    ],
};

const EMPTY_SCHEDULE = {
    schema_version: 1,
    program: { id: 'prg_1', name: 'Informatyka' },
    source: { version: 'v1', fetched_at: '', timezone: 'Europe/Warsaw' },
    items: [],
};

describe('PlanPage', () => {
    let component: PlanPage;
    let fixture: ComponentFixture<PlanPage>;
    let http: HttpTestingController;

    /** Opens the page on a plan, as a shared link would. */
    async function openPlan() {
        await TestBed.inject(Router).navigate([], {
            queryParams: {
                program: 'prg_1',
                group: 'grp_2',
                elective: 'crs_3:grp_7',
                from: '2026-11-16',
                to: '2026-11-22',
            },
        });
        TestBed.tick();
    }

    beforeEach(async () => {
        // The page remembers the last plan; every test starts without one.
        localStorage.clear();
        await TestBed.configureTestingModule({
            imports: [PlanPage],
            providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
        }).compileComponents();

        fixture = TestBed.createComponent(PlanPage);
        component = fixture.componentInstance;
        fixture.detectChanges();
        http = TestBed.inject(HttpTestingController);
        http.expectOne('/api/v1/catalog').flush(CATALOG);
        TestBed.tick();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('asks the server for exactly the plan the URL describes', async () => {
        await openPlan();

        const { params } = http.expectOne((r) => r.url === '/api/v1/schedule').request;
        expect(params.get('program')).toBe('prg_1');
        expect(params.getAll('group')).toEqual(['grp_2']);
        expect(params.getAll('elective')).toEqual(['crs_3:grp_7']);
        expect(params.get('from')).toBe('2026-11-16');
        expect(params.get('to')).toBe('2026-11-22');
    });

    it('moves the window, and the URL, a week back', async () => {
        await openPlan();
        http.expectOne((r) => r.url === '/api/v1/schedule').flush(EMPTY_SCHEDULE);
        await fixture.whenStable();

        const router = TestBed.inject(Router);
        const navigated = firstValueFrom(
            router.events.pipe(filter((event) => event instanceof NavigationEnd)),
        );
        fixture.nativeElement.querySelector('.week-nav button').click();
        await navigated;
        TestBed.tick();

        const { params } = http.expectOne((r) => r.url === '/api/v1/schedule').request;
        expect(params.get('from')).toBe('2026-11-09');
        expect(params.get('to')).toBe('2026-11-15');

        const url = router.url;
        expect(url).toContain('from=2026-11-09');
        expect(url).toContain('to=2026-11-15');
        expect(url).toContain('program=prg_1');
    });
});
