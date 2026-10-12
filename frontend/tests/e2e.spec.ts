import { test, expect } from '@playwright/test';

test.describe('The Exam Timetable from Hell — E2E Application Flows', () => {
  test('navigates through core university administration modules', async ({ page }) => {
    await page.goto('/');

    // Check App Header
    await expect(page.locator('h1')).toContainText('The Exam Timetable from Hell');

    // Check Dashboard KPI values
    await expect(page.getByText('Examinations', { exact: true })).toBeVisible();
    await expect(page.getByText('Students Enrolled', { exact: true })).toBeVisible();
    await expect(page.getByText('Rooms Available', { exact: true })).toBeVisible();

    // Navigate to Timetable Calendar
    await page.click('text=Timetable Grid');
    await expect(page.getByText('Timetable Calendar & Schedules')).toBeVisible();

    // Navigate to Examinations Management
    await page.click('text=Examinations');
    await expect(page.getByText('Course Examinations Management')).toBeVisible();

    // Navigate to Optimization Engine
    await page.click('text=Optimization Engine');
    await expect(page.getByText('Google OR-Tools CP-SAT Scheduling Engine')).toBeVisible();

    // Navigate to Conflict Center
    await page.click('text=Conflict Center');
    await expect(page.getByText('Conflict Diagnostics & Feasibility Center')).toBeVisible();

    // Navigate to Analytics & Metrics
    await page.click('text=Quality & Metrics');
    await expect(page.getByText('Timetable Quality Metrics & Comparative Analytics')).toBeVisible();

    // Navigate to Data & Versions
    await page.click('text=Data & Versions');
    await expect(page.getByText('Data Management, Import/Export & Version History')).toBeVisible();
  });
});
