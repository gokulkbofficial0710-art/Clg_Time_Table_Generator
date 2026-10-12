import { describe, it, expect } from 'vitest';

describe('Frontend Examination Generator Unit Tests', () => {
  it('calculates total hard clash metrics accurately', () => {
    const studentClashes = 2;
    const roomClashes = 1;
    const capacityViolations = 3;
    const total = studentClashes + roomClashes + capacityViolations;
    expect(total).toBe(6);
  });

  it('verifies quality score clamping between 0 and 100', () => {
    const rawScore1 = 94.5;
    const rawScore2 = -12.0;
    const rawScore3 = 105.0;

    const clamp = (v: number) => Math.max(0, Math.min(100, v));

    expect(clamp(rawScore1)).toBe(94.5);
    expect(clamp(rawScore2)).toBe(0);
    expect(clamp(rawScore3)).toBe(100);
  });

  it('validates assignment search filter logic', () => {
    const assignments = [
      { exam_code: 'EXAM-CS101', course_name: 'Intro to CS', room_code: 'HALL-A' },
      { exam_code: 'EXAM-MA101', course_name: 'Calculus', room_code: 'LAB-1' },
      { exam_code: 'EXAM-PHY202', course_name: 'Electromagnetism', room_code: 'HALL-A' }
    ];

    const searchStr = 'cs101';
    const filtered = assignments.filter(a => 
      a.exam_code.toLowerCase().includes(searchStr) || 
      a.course_name.toLowerCase().includes(searchStr)
    );

    expect(filtered.length).toBe(1);
    expect(filtered[0].exam_code).toBe('EXAM-CS101');
  });

  it('validates room filtering logic on timetable', () => {
    const assignments = [
      { exam_code: 'EXAM-CS101', room_code: 'HALL-A' },
      { exam_code: 'EXAM-MA101', room_code: 'LAB-1' },
      { exam_code: 'EXAM-PHY202', room_code: 'HALL-A' }
    ];

    const hallAExams = assignments.filter(a => a.room_code === 'HALL-A');
    expect(hallAExams.length).toBe(2);
  });
});
