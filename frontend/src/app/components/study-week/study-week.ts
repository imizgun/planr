import { Component } from '@angular/core';

export type Weekday = 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday' | 'Sunday';
export const WEEKDAYS: Weekday[] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

@Component({
  imports: [],
  selector: 'app-study-week',
  styleUrl: './study-week.scss',
  templateUrl: './study-week.html',
})
export class StudyWeek {}
