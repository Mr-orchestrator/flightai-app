# FlightAI Playwright Test Suite

## What's Tested

### `api.spec.ts` — Backend API Tests (No Browser)
Runs against `http://localhost:8000` using Playwright's API request context.

| Group | Tests |
|-------|-------|
| Health & Root | `/`, `/health`, `/airports` |
| Authentication | Signup (valid + duplicate + missing fields), Login (valid + wrong password + unknown email), `/auth/me` (valid token + no token + invalid + malformed) |
| Trip Extraction | Dubai query, ambiguous query, missing fields |
| Flight Search | Unauthenticated, authenticated (saves history), invalid dates |
| Travel History | Returns history, 401 without auth, accumulates across searches |
| Package Generation | Authenticated, 401 without auth, missing fields, minimal request, multiple destinations |
| Fallback/Outage | Static fallback when LLMs fail, concurrent requests, malformed JSON, very large requests |
| Security | JWT tampering, SQL injection, XSS attempt |

### `frontend.spec.ts` — Full E2E Browser Tests
Runs Chromium against `http://localhost:3000`.

| Group | Tests |
|-------|-------|
| Home Page | Loads, navbar, Sign In button, search card, airports dropdown, packages section, login prompt for unauth |
| Auth Page | Navigation, login form, tab switcher, Sign Up extra fields, signup E2E, navbar user name, wrong password error, back button, redirect if authenticated |
| Flight Search UI | Inputs visible, loading state on search |
| Package Generation UI | Form visible when authenticated, generate button, cards appear after generation |
| Logout Flow | Logout returns to unauthenticated state |
| Responsive Design | Mobile (375px), tablet (768px), auth page mobile |
| Navigation | Packages link, logo link |

## Setup

### Prerequisites
```bash
# 1. PostgreSQL running with DATABASE_URL in .env
# 2. Backend running
cd "D:\Ai recommendor\.claude\worktrees\wonderful-mccarthy"
pip install -r requirements.txt
uvicorn api_server:app --port 8000 --reload

# 3. Frontend running (separate terminal)
cd frontend
npm run dev

# 4. Install Playwright browsers (first time only)
cd "D:\Ai recommendor\.claude\worktrees\wonderful-mccarthy"
npx playwright install chromium
```

### Required Environment Variables (.env)
```env
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/flightai
JWT_SECRET_KEY=your-secret-key-at-least-32-chars

# Optional (tests still run with fallbacks if missing)
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-gemini-key
AMADEUS_CLIENT_ID=your-amadeus-id
AMADEUS_CLIENT_SECRET=your-amadeus-secret
```

## Running Tests

```bash
# All tests (API + Frontend)
npx playwright test

# API tests only (no browser needed)
npx playwright test tests/api.spec.ts

# Frontend tests only
npx playwright test tests/frontend.spec.ts

# Specific test group
npx playwright test -g "Authentication"

# With HTML report
npx playwright test --reporter=html
npx playwright show-report

# Debug mode (headed browser)
npx playwright test --headed --slowmo=500

# Single test
npx playwright test -g "POST /auth/signup"
```

## Test Outages Being Tested

1. **No ANTHROPIC_API_KEY** → Falls back to Gemini → test verifies `model_used` != 'claude'
2. **No GOOGLE_API_KEY** → Falls back to static templates → test verifies `success=true` with static packages
3. **No AMADEUS credentials** → Flight search returns `success=false` gracefully
4. **Invalid JWT** → Returns 401 (not 500)
5. **DB connection failure** → App should return 500 with error, not hang
6. **Concurrent requests** → All resolve without timeout
7. **Malformed JSON input** → Returns 422, not crash
8. **Oversized input** → Returns 400/413, not hang
