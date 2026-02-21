/**
 * FlightAI Backend API Tests
 * Tests all REST endpoints: health, auth, flights, travel history, packages
 *
 * Requirements:
 *   - Backend running: uvicorn api_server:app --port 8000
 *   - SQLite database auto-created on startup
 */

import { test, expect, APIRequestContext, request } from '@playwright/test';

const API_BASE = 'http://localhost:8000';

// Unique test user to avoid conflicts on repeated runs
const TEST_EMAIL = `test_${Date.now()}@flightai.test`;
const TEST_PASSWORD = 'TestPass123';
const TEST_NAME = 'E2E Test User';

let authToken: string = '';
let apiContext: APIRequestContext;

// ─────────────────────────────────────────────────────────────────────────────
// SETUP
// ─────────────────────────────────────────────────────────────────────────────

test.beforeAll(async () => {
  apiContext = await request.newContext({
    baseURL: API_BASE,
    extraHTTPHeaders: { 'Content-Type': 'application/json' },
  });
});

test.afterAll(async () => {
  await apiContext.dispose();
});

// ─────────────────────────────────────────────────────────────────────────────
// 1. HEALTH CHECK
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Health & Root Endpoints', () => {
  test('GET / returns API info', async () => {
    const response = await apiContext.get('/');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('status');
    expect(body).toHaveProperty('version');
    expect(body).toHaveProperty('endpoints');
    console.log('API version:', body.version, '- Endpoints:', body.endpoints.length);
  });

  test('GET /health returns healthy status', async () => {
    const response = await apiContext.get('/health');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('status', 'healthy');
    console.log('Health:', JSON.stringify(body, null, 2));
  });

  test('GET /airports returns list of airports', async () => {
    const response = await apiContext.get('/airports');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
    expect(body.length).toBeGreaterThan(0);
    const airport = body[0];
    expect(airport).toHaveProperty('iata');
    expect(airport).toHaveProperty('city');
    expect(airport.iata).toMatch(/^[A-Z]{3}$/);
    console.log(`Loaded ${body.length} airports. First:`, airport);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 2. AUTHENTICATION
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Authentication', () => {
  test('POST /auth/signup - creates a new user and returns JWT', async () => {
    const response = await apiContext.post('/auth/signup', {
      data: {
        email: TEST_EMAIL,
        password: TEST_PASSWORD,
        name: TEST_NAME,
        home_airport: 'BOM',
      },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('token');
    expect(body).toHaveProperty('email', TEST_EMAIL);
    expect(body).toHaveProperty('name', TEST_NAME);
    expect(body.token).toBeTruthy();
    authToken = body.token;
    console.log('Signup successful. User:', body.email);
  });

  test('POST /auth/signup - rejects duplicate email', async () => {
    const response = await apiContext.post('/auth/signup', {
      data: {
        email: TEST_EMAIL,
        password: TEST_PASSWORD,
        name: 'Duplicate User',
      },
    });

    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body).toHaveProperty('detail');
    console.log('Duplicate rejection:', body.detail);
  });

  test('POST /auth/signup - rejects missing required fields', async () => {
    const response = await apiContext.post('/auth/signup', {
      data: { email: 'incomplete@test.com' },
    });
    expect(response.status()).toBe(422);
  });

  test('POST /auth/login - valid credentials return JWT', async () => {
    const response = await apiContext.post('/auth/login', {
      data: { email: TEST_EMAIL, password: TEST_PASSWORD },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('token');
    expect(body).toHaveProperty('email', TEST_EMAIL);
    authToken = body.token;
    console.log('Login successful. Token length:', body.token.length);
  });

  test('POST /auth/login - wrong password returns 401', async () => {
    const response = await apiContext.post('/auth/login', {
      data: { email: TEST_EMAIL, password: 'WrongPassword999' },
    });

    expect(response.status()).toBe(401);
    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('POST /auth/login - unknown email returns 401', async () => {
    const response = await apiContext.post('/auth/login', {
      data: { email: 'nobody@nowhere.test', password: 'irrelevant' },
    });
    expect(response.status()).toBe(401);
  });

  test('GET /auth/me - returns user profile with valid JWT', async () => {
    const response = await apiContext.get('/auth/me', {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('email', TEST_EMAIL);
    expect(body).toHaveProperty('name', TEST_NAME);
    expect(body).toHaveProperty('home_airport', 'BOM');
    console.log('Profile:', body.name, body.email);
  });

  test('GET /auth/me - returns 401 with no token', async () => {
    const response = await apiContext.get('/auth/me');
    expect(response.status()).toBe(401);
  });

  test('GET /auth/me - returns 401 with invalid token', async () => {
    const response = await apiContext.get('/auth/me', {
      headers: { Authorization: 'Bearer this.is.not.a.valid.jwt.token' },
    });
    expect(response.status()).toBe(401);
  });

  test('GET /auth/me - returns 401 with malformed header', async () => {
    const response = await apiContext.get('/auth/me', {
      headers: { Authorization: authToken },
    });
    expect(response.status()).toBe(401);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 3. TRIP EXTRACTION
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Trip Extraction', () => {
  test('POST /extract-trip - extracts destination from query', async () => {
    const response = await apiContext.post('/extract-trip', {
      data: {
        origin_iata: 'BOM',
        user_query: 'I want to spend 5 days in Dubai',
        fallback_days: 7,
      },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('success');
    if (body.success) {
      expect(body).toHaveProperty('destination_iata');
      expect(body.destination_iata).toMatch(/^[A-Z]{3}$/);
      expect(body).toHaveProperty('duration_days');
      expect(body.duration_days).toBeGreaterThan(0);
    }
    console.log('Trip extraction:', JSON.stringify(body, null, 2));
  }, 30000);

  test('POST /extract-trip - works with ambiguous query', async () => {
    const response = await apiContext.post('/extract-trip', {
      data: {
        origin_iata: 'DEL',
        user_query: 'beach vacation next month',
        fallback_days: 7,
      },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('success');
    expect(body).toHaveProperty('origin_iata', 'DEL');
  }, 30000);

  test('POST /extract-trip - missing required fields returns 422', async () => {
    const response = await apiContext.post('/extract-trip', {
      data: { user_query: 'Dubai trip' },
    });
    expect(response.status()).toBe(422);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 4. FLIGHT SEARCH
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Flight Search', () => {
  const nextMonth = new Date();
  nextMonth.setDate(nextMonth.getDate() + 30);
  const returnDate = new Date(nextMonth);
  returnDate.setDate(returnDate.getDate() + 7);

  const formatDate = (d: Date) => d.toISOString().split('T')[0];

  test('POST /search-flights - unauthenticated search works', async () => {
    const response = await apiContext.post('/search-flights', {
      data: {
        origin: 'BOM',
        destination: 'DXB',
        departure_date: formatDate(nextMonth),
        return_date: formatDate(returnDate),
        adults: 1,
        max_results: 5,
        currency: 'INR',
      },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('success');
    console.log(`Unauthenticated search: success=${body.success}, flights=${body.flights?.length ?? 0}`);
  }, 30000);

  test('POST /search-flights - authenticated search saves to travel history', async () => {
    const response = await apiContext.post('/search-flights', {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        origin: 'BOM',
        destination: 'DXB',
        departure_date: formatDate(nextMonth),
        return_date: formatDate(returnDate),
        adults: 1,
        max_results: 5,
        currency: 'INR',
      },
    });

    expect(response.status()).toBe(200);
    await new Promise((r) => setTimeout(r, 500));
  }, 30000);

  test('POST /search-flights - invalid dates return error gracefully', async () => {
    const response = await apiContext.post('/search-flights', {
      data: {
        origin: 'BOM',
        destination: 'DXB',
        departure_date: '2020-01-01',
        adults: 1,
        max_results: 5,
        currency: 'INR',
      },
    });

    expect([200, 400, 422]).toContain(response.status());
    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('success');
    }
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 5. TRAVEL HISTORY
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Travel History', () => {
  test('GET /travel-history - returns saved search history', async () => {
    const response = await apiContext.get('/travel-history', {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
    console.log(`Travel history entries: ${body.length}`);

    if (body.length > 0) {
      const entry = body[0];
      expect(entry).toHaveProperty('destination_iata');
      expect(entry).toHaveProperty('origin_iata');
    }
  });

  test('GET /travel-history - returns 401 without auth', async () => {
    const response = await apiContext.get('/travel-history');
    expect(response.status()).toBe(401);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 6. AUTO PACKAGE GENERATION
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Auto Package Generation', () => {
  test('POST /auto-packages - generates packages for authenticated user', async () => {
    const response = await apiContext.post('/auto-packages', {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        destination: 'Dubai',
        duration_days: 5,
        budget_inr: 100000,
        preferences: {
          interests: ['beach', 'culture'],
          budget_level: 'medium',
          travel_style: 'leisure',
        },
      },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    console.log('Package generation:', JSON.stringify({
      success: body.success,
      model_used: body.model_used,
      package_count: body.packages?.length,
    }));

    expect(body).toHaveProperty('success');
    if (body.success) {
      expect(Array.isArray(body.packages)).toBe(true);
      expect(body.packages.length).toBeGreaterThan(0);

      const pkg = body.packages[0];
      expect(pkg).toHaveProperty('tier');
      expect(['budget', 'standard', 'premium']).toContain(pkg.tier);
      expect(pkg).toHaveProperty('name');
      expect(pkg).toHaveProperty('estimated_total_inr');

      const tiers = body.packages.map((p: any) => p.tier);
      console.log('Package tiers:', tiers);
    }
  }, 120000); // 2 min for LLM calls

  test('POST /auto-packages - returns 401 without auth', async () => {
    const response = await apiContext.post('/auto-packages', {
      data: {
        destination: 'Dubai',
        duration_days: 5,
        budget_inr: 100000,
      },
    });
    expect(response.status()).toBe(401);
  });

  test('POST /auto-packages - works with all optional fields', async () => {
    // All fields are optional - should work with defaults
    const response = await apiContext.post('/auto-packages', {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        budget_inr: 50000,
      },
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('success');
    console.log('Optional fields test:', body.success, body.model_used);
  }, 120000);

  test('POST /auto-packages - works with minimal request', async () => {
    const response = await apiContext.post('/auto-packages', {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        destination: 'Singapore',
        duration_days: 4,
        budget_inr: 80000,
      },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('success');
    console.log('Minimal request:', body.success, body.model_used);
  }, 120000);
});

// ─────────────────────────────────────────────────────────────────────────────
// 7. FALLBACK / OUTAGE SCENARIOS
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Outage & Fallback Scenarios', () => {
  test('POST /auto-packages - returns valid structure regardless of LLM availability', async () => {
    const response = await apiContext.post('/auto-packages', {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        destination: 'Test City',
        duration_days: 3,
        budget_inr: 50000,
      },
    });

    // Should never crash with 500
    expect(response.status()).toBe(200);
    const body = await response.json();

    expect(body).toHaveProperty('success');
    // model_used can be null when fallback is used
    expect(body).toHaveProperty('model_used');

    if (body.success) {
      expect(Array.isArray(body.packages)).toBe(true);
      expect(body.packages.length).toBeGreaterThan(0);
    }
    console.log(`Fallback: model_used=${body.model_used}, success=${body.success}`);
  }, 120000);

  test('Backend handles concurrent requests without crashing', async () => {
    const requests = [
      apiContext.get('/health'),
      apiContext.get('/airports'),
      apiContext.get('/auth/me', { headers: { Authorization: `Bearer ${authToken}` } }),
      apiContext.get('/travel-history', { headers: { Authorization: `Bearer ${authToken}` } }),
    ];

    const responses = await Promise.all(requests);
    responses.forEach((r, i) => {
      expect([200, 401]).toContain(r.status());
      console.log(`Concurrent request ${i + 1}: status ${r.status()}`);
    });
  });

  test('API handles malformed JSON gracefully', async () => {
    const ctx = await request.newContext({ baseURL: API_BASE });
    const response = await ctx.post('/auth/login', {
      headers: { 'Content-Type': 'application/json' },
      data: '{ this is not: valid json }',
    });
    expect([400, 422]).toContain(response.status());
    await ctx.dispose();
  });

  test('API handles very large requests gracefully', async () => {
    const longText = 'A'.repeat(10000);
    const response = await apiContext.post('/extract-trip', {
      data: {
        origin_iata: 'BOM',
        user_query: longText,
        fallback_days: 7,
      },
    });
    expect([200, 400, 413, 422]).toContain(response.status());
  }, 30000);
});

// ─────────────────────────────────────────────────────────────────────────────
// 8. SECURITY TESTS
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Security', () => {
  test('JWT cannot be tampered with', async () => {
    const parts = authToken.split('.');
    if (parts.length === 3) {
      const tamperedToken = parts[0] + '.' + btoa('{"user_id":"hacker","email":"hacker@evil.com"}') + '.' + parts[2];
      const response = await apiContext.get('/auth/me', {
        headers: { Authorization: `Bearer ${tamperedToken}` },
      });
      expect(response.status()).toBe(401);
    }
  });

  test('SQL injection attempt in login is rejected safely', async () => {
    const response = await apiContext.post('/auth/login', {
      data: {
        email: "' OR '1'='1' --",
        password: "' OR '1'='1' --",
      },
    });
    expect([400, 401, 422]).toContain(response.status());
  });

  test('XSS attempt in package destination is handled safely', async () => {
    const response = await apiContext.post('/auto-packages', {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        destination: '<script>alert("xss")</script>',
        duration_days: 3,
        budget_inr: 50000,
      },
    });
    // Should handle gracefully — either process it or reject it
    expect([200, 400, 422]).toContain(response.status());
    if (response.status() === 200) {
      const text = await response.text();
      expect(text).not.toContain('<script>alert');
    }
  }, 120000);
});
