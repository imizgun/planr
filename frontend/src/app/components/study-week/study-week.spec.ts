import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StudyWeek } from './study-week';

describe('StudyWeek', () => {
  let component: StudyWeek;
  let fixture: ComponentFixture<StudyWeek>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StudyWeek],
    }).compileComponents();

    fixture = TestBed.createComponent(StudyWeek);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
