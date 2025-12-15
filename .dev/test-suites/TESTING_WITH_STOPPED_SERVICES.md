# Testing Navigation UI Without Running Backend Services

**Date:** December 15, 2025  
**Issue:** All Azure Container Apps are **STOPPED** (scaled to zero)  
**Question:** How can navigation UI functions be tested if none of the ACA apps are running?

---

## Current Azure Environment Status

### Container Apps (All Stopped ❌)
```
Name                         Status    Replicas
---------------------------  --------  ----------
staging-env-temporal-server  Stopped   3
staging-env-temporal-ui      Stopped   2
staging-env-api              Stopped   1
staging-env-worker           Stopped   1
staging-env-zep              Stopped   2
```

**Scale-to-Zero:** These apps are configured to scale down to 0 replicas when idle to save costs.

### Static Web App (Running ✅)
```
Name:              staging-env-web
Status:            Standard
Default Hostname:  white-water-0d746bd0f.3.azurestaticapps.net
```

**Frontend:** The React Navigation UI is deployed and **accessible**.

---

## The Answer: Multiple Testing Strategies

You're absolutely right to question this! Here's how to test the navigation UI functions effectively:

### Strategy 1: Local Development Testing (RECOMMENDED for development)

**Run the full stack locally:**

```bash
# Terminal 1: Start local backend
cd backend
source venv/bin/activate
uvicorn backend.api.main:app --reload --port 8000

# Terminal 2: Start local frontend  
cd frontend
npm run dev
```

**Benefits:**
- ✅ Instant feedback
- ✅ Full control over all services
- ✅ No Azure costs
- ✅ Can debug backend + frontend simultaneously
- ✅ Test all navigation → API integrations

**What you can test:**
- All navigation routes and UI interactions
- API calls to backend endpoints
- Real-time data flow
- Error handling
- Form submissions

---

### Strategy 2: Trigger Azure Container Apps to Wake Up

**The staging environment uses scale-to-zero, but apps will automatically start when accessed:**

```bash
# Trigger the backend API to wake up
curl https://api.engram.work/health

# Trigger Temporal UI to wake up
curl https://[temporal-ui-fqdn].azurecontainerapps.io
```

**Timeline:**
- First request: ~30-60 seconds (cold start)
- Subsequent requests: Instant (while active)
- Auto-scale down: After 10-15 minutes of inactivity

**Benefits:**
- ✅ Test against real Azure infrastructure
- ✅ Verify actual deployment configuration
- ✅ Test custom domains and certificates
- ✅ Production-like environment

**Costs:**
- Only pay for active time (~$0.001/minute)
- Auto-scales back to $0 when idle

---

### Strategy 3: Frontend-Only UI Navigation Testing

**Test navigation structure without backend dependencies:**

**What can be tested without backend:**
- ✅ Navigation tree structure and organization
- ✅ Route transitions and URL handling
- ✅ Page loading and component rendering
- ✅ UI layout and responsiveness
- ✅ TreeNav expand/collapse behavior
- ✅ Error boundaries and loading states
- ✅ Browser history navigation

**E2E Tests (Playwright):**
```bash
# Run E2E tests against deployed frontend
npx playwright test .dev/test-suites/e2e/
```

**Example tests that work without backend:**
- Navigation tree renders correctly
- Routes map to correct pages
- Page components mount properly
- Links navigate to expected URLs
- UI state management works

**Limitations:**
- ❌ Cannot test API integration
- ❌ Cannot test real data loading
- ❌ Cannot test backend-dependent features

---

### Strategy 4: Mocked Backend Testing

**Use MSW (Mock Service Worker) or similar to simulate API responses:**

```typescript
// frontend/src/mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/v1/agents', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        agents: [
          { id: 'elena', name: 'Elena', status: 'active' },
          { id: 'marcus', name: 'Marcus', status: 'idle' }
        ]
      })
    );
  }),
  // ... more handlers
];
```

**Benefits:**
- ✅ Test UI with predictable data
- ✅ Test error scenarios
- ✅ No backend needed
- ✅ Fast test execution
- ✅ Can test edge cases

---

## Recommended Testing Workflow

### Phase 1: Development (Local)
```bash
# Run full stack locally for rapid iteration
npm run dev          # Frontend at localhost:5173
python backend       # Backend at localhost:8000
```

### Phase 2: Integration (Staging with Wake-Up)
```bash
# Deploy frontend changes
git push origin main  # Triggers GitHub Actions

# Wake up staging backend
curl https://api.engram.work/health

# Run E2E tests against staging
npx playwright test --config=playwright.config.staging.ts
```

### Phase 3: UI-Only (Static Web App)
```bash
# Test navigation structure without backend
npx playwright test .dev/test-suites/e2e/navigation.spec.ts
```

---

## Fixing the "Apps Are Stopped" Problem

### Option A: Keep Apps Warm (Costs Money)
```bicep
// In infra/modules/backend-aca.bicep
scale: {
  minReplicas: 1  // Always keep 1 replica running
  maxReplicas: 10
}
```

**Cost Impact:** ~$50-100/month (no longer scale-to-zero)

### Option B: Use a Keep-Alive Script (Cheaper)
```bash
# .dev/scripts/keep-staging-warm.sh
while true; do
  curl -s https://api.engram.work/health > /dev/null
  echo "Pinged at $(date)"
  sleep 300  # Every 5 minutes
done
```

**Cost Impact:** Minimal, apps stay warm only during active testing

### Option C: Embrace Scale-to-Zero (Current, Cheapest)
- Accept 30-60s cold start on first request
- Perfect for POC/staging environment
- Use local development for most testing

---

## Current Test Suite Capabilities

### Unit Tests (Backend)
```bash
cd .dev/test-suites/unit/
pytest -v
```
**Status:** Can run WITHOUT Azure services
**Requirements:** Local Python environment only

### E2E Tests (Frontend + Backend)
```bash
cd .dev/test-suites/e2e/
npx playwright test
```
**Status:** REQUIRES backend to be running (local or Azure)
**Current State:** Will fail if backend is stopped

### Integration Tests
```bash
cd .dev/test-suites/integration/
pytest -v
```
**Status:** REQUIRES backend services running
**Current State:** Will fail if services are stopped

---

## Immediate Recommendations

### 1. Update E2E Tests to Handle Cold Starts
```typescript
// Add retry logic for cold starts
test('should load agents page', async ({ page }) => {
  // Wait up to 90 seconds for cold start
  await page.goto('/agents', { timeout: 90000 });
  await expect(page.locator('h1')).toContainText('Agents');
});
```

### 2. Create a Pre-Test Warm-Up Script
```bash
# .dev/scripts/warm-up-staging.sh
#!/bin/bash
echo "Warming up staging environment..."
curl -s https://api.engram.work/health
curl -s https://api.engram.work/api/v1/agents
echo "Environment ready for testing!"
```

### 3. Document the Testing Strategy
Create different test commands for different scenarios:
```json
{
  "scripts": {
    "test:local": "Run tests against local dev environment",
    "test:staging": "Wake up staging + run tests",
    "test:ui-only": "Test navigation without backend",
    "test:e2e:full": "Full integration tests (requires running backend)"
  }
}
```

---

## Summary

**Direct Answer:** You CAN'T fully test navigation UI functions if backend services aren't running, BUT you have several strategies:

1. **Best for development:** Run everything locally
2. **Best for staging validation:** Trigger wake-up + test (30-60s delay)
3. **Best for UI-only:** Test navigation structure without backend
4. **Best for predictability:** Use mocked backend responses

**The scale-to-zero configuration is intentional and cost-effective for POC/staging, but requires testing strategies that account for cold starts.**

Would you like me to create warm-up scripts or update the test configuration to handle cold starts automatically?
