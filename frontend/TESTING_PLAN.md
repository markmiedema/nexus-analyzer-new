# Frontend Testing Plan - Phase 2

**Status**: Deferred to Phase 2
**Last Updated**: 2025-10-22

## Current Testing Strategy (Phase 1)

Phase 1 focuses on foundational quality checks:

✅ **Type Safety** - TypeScript compilation enforces type correctness
✅ **Build Verification** - Production build ensures components are valid
✅ **Lint Checking** - ESLint catches common issues
✅ **CI/CD Integration** - Automated checks on every push

## Planned Testing Strategy (Phase 2)

### 1. Unit Testing with Jest & React Testing Library

**Scope**: Component-level testing
**Tools**:
- Jest (test runner)
- React Testing Library (component testing)
- @testing-library/user-event (user interaction simulation)

**Target Coverage**:
- Form components (BusinessProfileForm, etc.)
- Display components (AnalysisStatusTracker, ReportViewer)
- Utility functions (api.ts, formatters)
- Context providers (AuthContext)

**Example Test Structure**:
```typescript
// components/__tests__/BusinessProfileForm.test.tsx
describe('BusinessProfileForm', () => {
  it('validates EIN format', () => {
    // Test EIN validation logic
  });

  it('submits valid business profile', async () => {
    // Test form submission
  });

  it('displays validation errors', () => {
    // Test error display
  });
});
```

### 2. Integration Testing

**Scope**: Multi-component workflows
**Tools**:
- React Testing Library
- MSW (Mock Service Worker) for API mocking

**Target Scenarios**:
- Complete analysis creation workflow
- Authentication flow (login/logout)
- Data fetching and display
- Error handling and retry logic

### 3. End-to-End Testing with Playwright

**Scope**: Full user journeys
**Tools**: Playwright

**Target Journeys**:
- User registration and login
- Create new analysis (upload CSV → view results)
- Generate and download reports
- Multi-tenant isolation

**Example E2E Test**:
```typescript
// e2e/analysis-workflow.spec.ts
test('complete analysis workflow', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  await page.goto('/dashboard/analyses/new');
  // ... continue workflow
});
```

### 4. Visual Regression Testing

**Scope**: UI consistency
**Tools**:
- Playwright screenshots
- Percy or Chromatic

**Target Components**:
- Dashboard views
- Forms
- Reports
- Charts and visualizations

## Testing Metrics & Goals

**Phase 2 Targets**:
- **Unit Test Coverage**: 80%+ for utilities and business logic
- **Component Coverage**: 70%+ for React components
- **E2E Coverage**: 10+ critical user journeys
- **CI Integration**: All tests run on every PR

## Implementation Timeline

**Phase 2.1 - Foundation** (Week 1-2):
- Set up Jest and React Testing Library
- Add test utilities and helpers
- Write first 10-15 component tests
- Configure coverage reporting

**Phase 2.2 - Expansion** (Week 3-4):
- Add integration tests with MSW
- Write remaining component tests
- Set up Playwright
- Create first E2E tests

**Phase 2.3 - Refinement** (Week 5-6):
- Achieve coverage targets
- Add visual regression tests
- Document testing best practices
- Train team on testing approach

## Configuration Files to Add

```javascript
// jest.config.js
module.exports = {
  preset: 'next/jest',
  testEnvironment: 'jest-environment-jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'app/**/*.{js,jsx,ts,tsx}',
    'components/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
};
```

```javascript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
});
```

## Dependencies to Add

```json
{
  "devDependencies": {
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5",
    "@testing-library/user-event": "^14.5.1",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "@playwright/test": "^1.40.0",
    "msw": "^2.0.0"
  }
}
```

## Why Deferred to Phase 2?

**Phase 1 Priorities**:
1. ✅ Core functionality implementation
2. ✅ Type safety and build verification
3. ✅ CI/CD pipeline setup
4. ✅ Backend testing infrastructure

**Phase 2 Additions**:
1. 🔲 Frontend test coverage
2. 🔲 E2E user journey validation
3. 🔲 Visual regression prevention

**Rationale**:
- TypeScript provides strong compile-time safety
- Build verification catches integration issues
- Backend has comprehensive test coverage
- Frontend tests add value but aren't blocking Phase 2 feature development
- Can add tests incrementally alongside new features

## Success Criteria

Phase 2 frontend testing will be considered complete when:

1. ✅ Jest and React Testing Library configured
2. ✅ 80%+ coverage for utilities and business logic
3. ✅ 70%+ coverage for React components
4. ✅ 10+ E2E tests covering critical paths
5. ✅ Tests run in CI on every PR
6. ✅ Team trained on testing practices
7. ✅ Testing documentation complete

---

**Next Steps**:
- Review and approve this plan
- Schedule Phase 2 testing sprint
- Allocate resources for test development
- Set up monitoring for test metrics
