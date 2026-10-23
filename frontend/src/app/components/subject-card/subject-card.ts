import { Component } from '@angular/core';
import { Weekday } from '../study-week/study-week';

export interface SubjectCard {
  id: string,
  course: Course,
  type: 'labaratorium' | 'wykład' | 'ćwiczenia' | 'konwersatorium',
  group: Group,
  teachers: Teacher[],
  room: string,
  mode: 'stationary' | 'online',
  weekday: Weekday,
  starTime: string, // time string
  endTime: string, // time string
  dateFrom: string,
  dateTo: string
}

interface Course {
  id: string,
  name: string
}

interface Group {
  id: string,
  label: string,
  is_program_wide: boolean
}

interface Teacher {
  id: string,
  name: string
}

@Component({
  imports: [],
  selector: 'app-subject-card',
  styleUrl: './subject-card.scss',
  templateUrl: './subject-card.html',
})
export class SubjectCard {}
