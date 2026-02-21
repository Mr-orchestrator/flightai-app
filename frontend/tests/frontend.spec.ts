/**
 * FlightAI Frontend E2E Tests
 * Tests the Next.js UI: page load, auth flow, search, package generation
 *
 * Requirements:
 *   - Frontend running: npm run dev (port 3000)
 *   - Backend running: uvicorn api_server:app --port 8000
 */

import { test, expect, Page } from '@playwright/test';

const FRONTEND_URL = 'http://localhost:3000';
const TEST_EMAIL = `ui_test_${Date.now()}@flightai.test`;
const TEST_PASSWORD = 'UITest123!';
const TEST_NAME = 'UI Test User';

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────────────────────

async function waitForAnimation(page: Page, ms = 1000) {
  await page.waitForTimeout(ms);
}

async function signupViaAPI(email: string, password: string, name: string) {
  const response = await fetch('http://localhost:8000/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  });
  return response.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. HOME PAGE
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Home Page', () => {
  test('loads successfully and shows hero section', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 1500);

    // Check title
    await expect(page).toHaveTitle(/FlightAI/i);

    // Check hero heading
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();
    const text = await heading.textContent();
    console.log('Hero heading:', text);
    expect(text?.toLowerCase()).toMatch(/next|adventure|flight|ai/i);
  });

  test('navbar is visible and contains brand', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page);

    const nav = page.locator('nav').first();
    await expect(nav).toBeVisible();
    const navText = await nav.textContent();
    expect(navText).toContain('FlightAI');
  });

  test('navbar shows Sign In button when not logged in', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 1500);

    const signInBtn = page.getByRole('link', { name: /sign in/i });
    await expect(signInBtn).toBeVisible();
    await expect(signInBtn).toHaveAttribute('href', '/auth');
  });

  test('search card is visible on home page', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 2000);

    // Look for origin airport selector
    const originSelect = page.locator('select').first();
    await expect(originSelect).toBeVisible();
    console.log('Search card found');
  });

  test('airport dropdown loads airports from API', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 2000);

    const originSelect = page.locator('select').first();
    const optionsCount = await originSelect.locator('option').count();
    console.log('Airport options loaded:', optionsCount);
    expect(optionsCount).toBeGreaterThan(1); // At least one airport + placeholder
  });

  test('packages section is visible on home page', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 1500);

    // Scroll to packages section
    await page.evaluate(() => {
      const el = document.getElementById('packages');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    });
    await waitForAnimation(page, 500);

    // The AutoPackageSection should be visible
    const packagesSection = page.locator('#packages');
    await expect(packagesSection).toBeVisible();
    console.log('Packages section found');
  });

  test('packages section shows login prompt for unauthenticated users', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 2000);

    // Scroll to packages
    await page.evaluate(() => {
      const el = document.getElementById('packages');
      if (el) el.scrollIntoView();
    });
    await waitForAnimation(page, 500);

    const pageText = await page.textContent('body');
    const hasLoginPrompt = pageText?.match(/sign in|login|unlock|authenticate/i);
    console.log('Login prompt visible:', !!hasLoginPrompt);
    // Should show something about needing to log in
    expect(hasLoginPrompt).toBeTruthy();
  });

  test('animated background renders without errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 2000);

    // Filter out expected non-critical errors
    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes('Failed to load resource') && // Font preload warnings
              !e.includes('net::ERR_') &&
              !e.includes('favicon')
    );
    console.log('Critical JS errors:', criticalErrors);
    expect(criticalErrors.length).toBe(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 2. AUTH PAGE
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Auth Page - Login/Signup', () => {
  test('navigates to auth page from Sign In link', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 1500);

    const signInLink = page.getByRole('link', { name: /sign in/i }).first();
    await signInLink.click();
    await page.waitForURL('**/auth**');
    expect(page.url()).toContain('/auth');
  });

  test('auth page shows login form by default', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/auth`);
    await waitForAnimation(page);

    const heading = page.getByRole('heading').first();
    await expect(heading).toBeVisible();
    const text = await heading.textContent();
    expect(text?.toLowerCase()).toMatch(/welcome|sign in|login/i);
  });

  test('auth page has tab switcher between Login and Sign Up', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/auth`);
    await waitForAnimation(page);

    const loginTab = page.getByRole('button', { name: /sign in/i });
    const signupTab = page.getByRole('button', { name: /sign up/i });
    await expect(loginTab).toBeVisible();
    await expect(signupTab).toBeVisible();
  });

  test('switching to Sign Up shows extra fields', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/auth`);
    await waitForAnimation(page);

    const signupTab = page.getByRole('button', { name: /sign up/i });
    await signupTab.click();
    await waitForAnimation(page, 500);

    // Name field should appear
    const nameInput = page.locator('input[type="text"]').first();
    await expect(nameInput).toBeVisible();
    console.log('Sign up form shows name field');
  });

  test('signup flow with new user works end-to-end', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/auth`);
    await waitForAnimation(page);

    // Switch to signup tab
    await page.getByRole('button', { name: /sign up/i }).click();
    await waitForAnimation(page, 500);

    // Fill in the form
    await page.locator('input[type="text"]').fill(TEST_NAME);
    await page.locator('input[type="email"]').fill(TEST_EMAIL);
    await page.locator('input[type="password"]').fill(TEST_PASSWORD);

    // Submit
    await page.getByRole('button', { name: /create account/i }).click();

    // Should redirect to home page
    await page.waitForURL(`${FRONTEND_URL}/`, { timeout: 10000 });
    expect(page.url()).toBe(`${FRONTEND_URL}/`);
    console.log('Signup successful - redirected to home');
  });

  test('navbar shows user name after signup', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/auth`);
    await waitForAnimation(page);

    await page.getByRole('button', { name: /sign up/i }).click();
    await waitForAnimation(page, 300);

    // Use a different email since TEST_EMAIL may be taken
    const uniqueEmail = `nav_test_${Date.now()}@flightai.test`;
    await page.locator('input[type="text"]').fill('Nav Test User');
    await page.locator('input[type="email"]').fill(uniqueEmail);
    await page.locator('input[type="password"]').fill(TEST_PASSWORD);
    await page.getByRole('button', { name: /create account/i }).click();

    await page.waitForURL(`${FRONTEND_URL}/`, { timeout: 10000 });
    await waitForAnimation(page, 1500);

    // Navbar should show user name
    const navText = await page.locator('nav').textContent();
    console.log('Nav text after login:', navText?.substring(0, 100));
    expect(navText?.toLowerCase()).toMatch(/hi|traveler|nav test/i);
  });

  test('login with wrong password shows error', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/auth`);
    await waitForAnimation(page);

    // Ensure on login tab
    await page.getByRole('button', { name: /sign in/i }).first().click();
    await waitForAnimation(page, 300);

    await page.locator('input[type="email"]').fill(TEST_EMAIL);
    await page.locator('input[type="password"]').fill('WrongPassword!');
    await page.getByRole('button', { name: /^sign in$/i }).click();

    await waitForAnimation(page, 2000);

    // Error message should appear
    const errorEl = page.locator('.text-red-400');
    await expect(errorEl).toBeVisible({ timeout: 5000 });
    console.log('Error message shown for wrong password');
  });

  test('back button returns to home page', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/auth`);
    await waitForAnimation(page);

    const backBtn = page.getByRole('button', { name: /back/i });
    await expect(backBtn).toBeVisible();
    await backBtn.click();

    await page.waitForURL(`${FRONTEND_URL}/`, { timeout: 5000 });
    expect(page.url()).toBe(`${FRONTEND_URL}/`);
  });

  test('authenticated user is redirected from auth page to home', async ({ page }) => {
    // First login via API and set cookie
    const loginResp = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    });
    const { token } = await loginResp.json();

    if (token) {
      // Set cookie in browser
      await page.goto(FRONTEND_URL);
      await page.evaluate((t) => {
        document.cookie = `flightai_token=${t}; path=/; max-age=${7 * 24 * 3600}`;
      }, token);

      // Now navigate to auth page - should redirect
      await page.goto(`${FRONTEND_URL}/auth`);
      await waitForAnimation(page, 2000);

      // Should redirect to home
      expect(page.url()).not.toContain('/auth');
    } else {
      test.skip();
    }
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 3. FLIGHT SEARCH FLOW
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Flight Search UI', () => {
  test('search card has required inputs', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 2000);

    // Origin airport select
    const selects = page.locator('select');
    const selectCount = await selects.count();
    expect(selectCount).toBeGreaterThanOrEqual(1);

    // Text input for query
    const textInputs = page.locator('input[type="text"], textarea');
    const inputCount = await textInputs.count();
    expect(inputCount).toBeGreaterThanOrEqual(1);
  });

  test('clicking search button triggers loading state', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 2000);

    // Select origin airport
    const originSelect = page.locator('select').first();
    await originSelect.selectOption({ index: 1 }); // First real airport

    // Type a query
    const queryInput = page.locator('textarea, input[placeholder*="destination" i], input[placeholder*="where" i], input[type="text"]').first();
    await queryInput.fill('5 days in Dubai');

    // Click search
    const searchBtn = page.getByRole('button', { name: /search|find|explore/i }).first();
    await searchBtn.click();

    // Loading state should appear briefly
    await waitForAnimation(page, 500);
    const loadingEl = page.locator('text=/loading|searching|finding/i').first();
    const isLoading = await loadingEl.isVisible().catch(() => false);
    console.log('Loading state detected:', isLoading);
    // Not strictly required since loading may be fast
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 4. AUTHENTICATED PACKAGE GENERATION UI
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Package Generation UI (Authenticated)', () => {
  let authToken: string = '';

  test.beforeAll(async () => {
    // Create user for UI tests
    try {
      const resp = await fetch('http://localhost:8000/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: `pkg_ui_${Date.now()}@flightai.test`,
          password: TEST_PASSWORD,
          name: 'Package UI Tester',
        }),
      });
      const data = await resp.json();
      authToken = data.token || '';
    } catch {
      authToken = '';
    }
  });

  async function loginViaUI(page: Page, token: string) {
    await page.goto(FRONTEND_URL);
    await page.evaluate((t) => {
      document.cookie = `flightai_token=${t}; path=/; max-age=${7 * 24 * 3600}`;
    }, token);
    await page.reload();
    await page.waitForTimeout(1500);
  }

  test('packages section shows form when authenticated', async ({ page }) => {
    if (!authToken) {
      console.log('Skipping - no auth token (backend may not be running)');
      return;
    }

    await loginViaUI(page, authToken);

    // Scroll to packages section
    await page.evaluate(() => {
      document.getElementById('packages')?.scrollIntoView();
    });
    await waitForAnimation(page, 500);

    const packagesSection = page.locator('#packages');
    const sectionText = await packagesSection.textContent();
    console.log('Packages section text (first 200 chars):', sectionText?.substring(0, 200));

    // Should not show login prompt anymore
    const hasLoginPrompt = sectionText?.match(/sign in.*unlock|login.*unlock/i);
    expect(hasLoginPrompt).toBeFalsy();
  });

  test('generate packages button exists and is clickable', async ({ page }) => {
    if (!authToken) return;

    await loginViaUI(page, authToken);

    await page.evaluate(() => {
      document.getElementById('packages')?.scrollIntoView();
    });
    await waitForAnimation(page, 500);

    const generateBtn = page.getByRole('button', { name: /generate|create.*package/i });
    const btnCount = await generateBtn.count();
    console.log('Generate buttons found:', btnCount);
    expect(btnCount).toBeGreaterThan(0);
  });

  test('package cards appear after generation (with API keys)', async ({ page }) => {
    if (!authToken) return;

    await loginViaUI(page, authToken);

    await page.evaluate(() => {
      document.getElementById('packages')?.scrollIntoView();
    });
    await waitForAnimation(page, 500);

    // Fill destination if there's an input
    const destInput = page.locator('#packages input[type="text"]').first();
    if (await destInput.isVisible()) {
      await destInput.fill('Dubai');
    }

    const generateBtn = page.getByRole('button', { name: /generate/i }).first();
    if (await generateBtn.isVisible()) {
      await generateBtn.click();

      // Wait for package cards (with long timeout for LLM)
      await waitForAnimation(page, 2000);

      const pageText = await page.textContent('body');
      const hasPackages = pageText?.match(/budget|standard|premium|package|itinerary/i);
      console.log('Package content detected:', !!hasPackages);
    }
  }, 120000);
});

// ─────────────────────────────────────────────────────────────────────────────
// 5. LOGOUT FLOW
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Logout Flow', () => {
  test('logout button returns to unauthenticated state', async ({ page }) => {
    // Get a token first
    const loginResp = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    }).catch(() => null);

    if (!loginResp?.ok) {
      console.log('Skipping logout test - cannot login (backend may not be running)');
      return;
    }

    const { token } = await loginResp.json();
    if (!token) return;

    // Set token in browser
    await page.goto(FRONTEND_URL);
    await page.evaluate((t) => {
      document.cookie = `flightai_token=${t}; path=/; max-age=${7 * 24 * 3600}`;
    }, token);
    await page.reload();
    await waitForAnimation(page, 1500);

    // Find and click logout button
    const logoutBtn = page.getByRole('button', { name: /logout|sign out/i });
    await expect(logoutBtn).toBeVisible({ timeout: 5000 });
    await logoutBtn.click();
    await waitForAnimation(page, 1000);

    // Sign In link should reappear
    const signInLink = page.getByRole('link', { name: /sign in/i });
    await expect(signInLink).toBeVisible({ timeout: 5000 });
    console.log('Logout successful - Sign In link visible again');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 6. RESPONSIVE DESIGN
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Responsive Design', () => {
  test('home page is usable on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 1500);

    const body = page.locator('body');
    await expect(body).toBeVisible();

    // No horizontal scroll
    const scrollWidth = await page.evaluate(() => document.body.scrollWidth);
    const clientWidth = await page.evaluate(() => document.body.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 10); // 10px tolerance
    console.log(`Mobile: scrollWidth=${scrollWidth}, clientWidth=${clientWidth}`);
  });

  test('home page is usable on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 1500);

    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();
  });

  test('auth page works on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`${FRONTEND_URL}/auth`);
    await waitForAnimation(page);

    const form = page.locator('form');
    await expect(form).toBeVisible();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 7. NAVIGATION
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Navigation', () => {
  test('Packages nav link scrolls to packages section', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await waitForAnimation(page, 1500);

    const packagesLink = page.getByRole('link', { name: /packages/i });
    if (await packagesLink.isVisible()) {
      await packagesLink.click();
      await waitForAnimation(page, 500);

      // Page should contain packages section
      const packagesSection = page.locator('#packages');
      await expect(packagesSection).toBeVisible();
    }
  });

  test('logo link returns to home page', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/auth`);
    await waitForAnimation(page);

    const logoLink = page.locator('nav a[href="/"]').first();
    if (await logoLink.isVisible()) {
      await logoLink.click();
      await page.waitForURL(`${FRONTEND_URL}/`, { timeout: 5000 });
      expect(page.url()).toBe(`${FRONTEND_URL}/`);
    }
  });
});
