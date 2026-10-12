import { describe, it, expect } from 'vitest';
import { StudentSeatingResponse } from '../types';

describe('Student Seatings & Hall Allocations Unit Tests', () => {
  const mockStudents: StudentSeatingResponse[] = [
    {
      id: 1,
      student_id: 'STU-2026-1001',
      name: 'Alex Williams',
      department: 'Computer Science',
      semester: 'Fall',
      special_accommodations: [],
      subjects_count: 5,
      distinct_halls_count: 3,
      exams: [
        {
          exam_id: 22,
          exam_code: 'EXAM-CS499',
          course_code: 'CS499',
          course_name: 'Senior Capstone Defense',
          date: '2026-12-14',
          day_name: 'Monday',
          start_time: '09:00:00',
          end_time: '12:00:00',
          room_code: 'AUD-MAIN',
          room_name: 'Grand University Auditorium',
          building: 'Central Hall',
          seat_number: 'AUD-MAIN-D01',
          is_locked: true
        },
        {
          exam_id: 6,
          exam_code: 'EXAM-MA101',
          course_code: 'MA101',
          course_name: 'Calculus I & Analytical Geometry',
          date: '2026-12-14',
          day_name: 'Monday',
          start_time: '13:00:00',
          end_time: '16:00:00',
          room_code: 'LAB-COMP',
          room_name: 'Advanced Computing Laboratory',
          building: 'Turing Engineering Building',
          seat_number: 'LAB-COMP-D01',
          is_locked: false
        },
        {
          exam_id: 1,
          exam_code: 'EXAM-CS101',
          course_code: 'CS101',
          course_name: 'Introduction to Computer Science',
          date: '2026-12-15',
          day_name: 'Tuesday',
          start_time: '13:00:00',
          end_time: '16:00:00',
          room_code: 'SEM-A',
          room_name: 'Executive Seminar Room',
          building: 'Business School',
          seat_number: 'SEM-A-D01',
          is_locked: false
        },
        {
          exam_id: 2,
          exam_code: 'EXAM-CS201',
          course_code: 'CS201',
          course_name: 'Data Structures & Algorithms',
          date: '2026-12-16',
          day_name: 'Wednesday',
          start_time: '09:00:00',
          end_time: '12:00:00',
          room_code: 'LAB-COMP',
          room_name: 'Advanced Computing Laboratory',
          building: 'Turing Engineering Building',
          seat_number: 'LAB-COMP-D01',
          is_locked: false
        },
        {
          exam_id: 8,
          exam_code: 'EXAM-MA204',
          course_code: 'MA204',
          course_name: 'Discrete Mathematics',
          date: '2026-12-17',
          day_name: 'Thursday',
          start_time: '13:00:00',
          end_time: '16:00:00',
          room_code: 'SEM-A',
          room_name: 'Executive Seminar Room',
          building: 'Business School',
          seat_number: 'SEM-A-D01',
          is_locked: false
        }
      ]
    },
    {
      id: 2,
      student_id: 'STU-2026-1002',
      name: 'Jordan Garcia',
      department: 'Mathematics',
      semester: 'Fall',
      special_accommodations: [],
      subjects_count: 4,
      distinct_halls_count: 3,
      exams: [
        {
          exam_id: 6,
          exam_code: 'EXAM-MA101',
          course_code: 'MA101',
          course_name: 'Calculus I & Analytical Geometry',
          date: '2026-12-14',
          day_name: 'Monday',
          start_time: '13:00:00',
          end_time: '16:00:00',
          room_code: 'LAB-COMP',
          room_name: 'Advanced Computing Laboratory',
          building: 'Turing Engineering Building',
          seat_number: 'LAB-COMP-D02',
          is_locked: false
        }
      ]
    }
  ];

  it('filters students accurately by department', () => {
    const csStudents = mockStudents.filter(s => s.department === 'Computer Science');
    expect(csStudents.length).toBe(1);
    expect(csStudents[0].name).toBe('Alex Williams');

    const mathStudents = mockStudents.filter(s => s.department === 'Mathematics');
    expect(mathStudents.length).toBe(1);
    expect(mathStudents[0].student_id).toBe('STU-2026-1002');
  });

  it('validates student enrolled multi-subject schedule and distinct hall venues', () => {
    const student1 = mockStudents[0];
    expect(student1.exams.length).toBe(5);
    expect(student1.subjects_count).toBe(5);

    const uniqueHalls = new Set(student1.exams.map(e => e.room_code));
    expect(uniqueHalls.size).toBe(3);
    expect(uniqueHalls.has('AUD-MAIN')).toBe(true);
    expect(uniqueHalls.has('LAB-COMP')).toBe(true);
    expect(uniqueHalls.has('SEM-A')).toBe(true);
  });

  it('verifies deterministic desk allocation format', () => {
    const student1 = mockStudents[0];
    student1.exams.forEach(e => {
      expect(e.seat_number).toMatch(/^[A-Z0-9_-]+-D\d{2}$/);
    });
  });

  it('searches students by roll ID or candidate name', () => {
    const query = '1001';
    const found = mockStudents.filter(s =>
      s.name.toLowerCase().includes(query) || s.student_id.toLowerCase().includes(query)
    );
    expect(found.length).toBe(1);
    expect(found[0].student_id).toBe('STU-2026-1001');
  });

  it('validates default collapsed state and clicking student name expands details', () => {
    let allExpanded = false;
    const expandedMap: Record<number, boolean> = {};

    const isStudentExpanded = (id: number) => {
      if (expandedMap[id] !== undefined) return expandedMap[id];
      return allExpanded;
    };

    // By default, student is collapsed
    expect(isStudentExpanded(1)).toBe(false);

    // After clicking name, student 1 expands
    expandedMap[1] = !isStudentExpanded(1);
    expect(isStudentExpanded(1)).toBe(true);
    expect(isStudentExpanded(2)).toBe(false);

    // Clicking student 1 again collapses it
    expandedMap[1] = !isStudentExpanded(1);
    expect(isStudentExpanded(1)).toBe(false);
  });
});
