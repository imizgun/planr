import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { PlanPage } from './plan-page';

describe('PlanPage', () => {
    let component: PlanPage;
    let fixture: ComponentFixture<PlanPage>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [PlanPage],
            providers: [provideHttpClient(), provideHttpClientTesting()],
        }).compileComponents();

        fixture = TestBed.createComponent(PlanPage);
        component = fixture.componentInstance;
        fixture.detectChanges();
        TestBed.inject(HttpTestingController)
            .expectOne('/api/v1/catalog')
            .flush({ schema_version: 1, source: { version: 'v1', fetched_at: '' }, programs: [] });
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
