# Doctor Doom Frontend

React/TypeScript SPA for thermal panel inspection monitoring and management.

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 19 + TypeScript 5.x | Type-safe component development |
| Build Tool | Vite 6 | Fast HMR, ESM-native builds |
| State Management | Zustand + React Query | Global state + server cache |
| Styling | Tailwind CSS 4 | Utility-first design system |
| Map Engine | Deck.gl + Mapbox GL JS | GPU-accelerated geospatial rendering |
| Charting | Recharts + D3.js | Declarative charts |
| Thermal Viewer | Custom WebGL Canvas | 16-bit thermal image rendering |
| 3D Visualization | Three.js + R3F | 3D array model with thermal overlay |
| Testing | Vitest + Playwright | Unit, integration, E2E coverage |

## Quick Start

### Prerequisites

- Node.js 20+
- npm or pnpm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
# Start dev server (with proxy to backend)
npm run dev

# Open http://localhost:3000
```

### Build

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

### Testing

```bash
# Unit tests
npm run test

# Unit tests with UI
npm run test:ui

# E2E tests
npm run test:e2e

# Coverage report
npm run test:coverage
```

### Linting & Formatting

```bash
# Lint
npm run lint

# Fix lint errors
npm run lint:fix

# Format code
npm run format
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/       # Layout components (Sidebar, Header)
│   │   ├── common/       # Reusable UI components
│   │   ├── thermal/      # Thermal image viewer
│   │   ├── map/          # Map components
│   │   ├── charts/       # Chart components
│   │   ├── defects/      # Defect-related components
│   │   ├── reports/      # Report components
│   │   └── flight/       # Flight planner components
│   ├── views/
│   │   ├── dashboard/    # Dashboard view
│   │   ├── array-map/    # Array map view
│   │   ├── defect-log/   # Defect log view
│   │   ├── module-inspector/ # Module inspector view
│   │   ├── comparison/   # Comparison view
│   │   ├── report-builder/   # Report builder view
│   │   └── flight-planner/   # Flight planner view
│   ├── hooks/            # Custom React hooks
│   ├── stores/           # Zustand stores
│   ├── services/         # API client
│   ├── types/            # TypeScript types
│   ├── utils/            # Utility functions
│   └── styles/           # Global styles
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # E2E tests
└── public/               # Static assets
```

## Key Views

### Dashboard
Fleet overview with health scores, recent inspections, and alert feed.

### Array Map
Interactive thermal heatmap with module-level drill-down and defect overlays.
- Deck.gl layers for defect visualization
- Mapbox satellite imagery
- Click to drill down to module details

### Defect Log
Sortable, filterable table with severity, ΔT, confidence, and photos.
- TanStack Table for sorting/filtering
- Severity badges
- Quick view modal

### Module Inspector
Side-by-side thermal + RGB with annotation tools and history.
- Custom WebGL thermal viewer
- Telemetry charts (Recharts)
- Defect history

### Comparison View
Before/after overlays across inspection dates for degradation tracking.
- Multi-inspection comparison
- Performance trend analysis

### Report Builder
Configure, preview, and export IEC 62446-3 compliant PDF reports.
- Report configuration form
- Recent reports list
- Download generated reports

### Flight Planner
Define survey area on map, auto-generate waypoint mission.
- Mapbox GL Draw for area selection
- Waypoint generation algorithm
- Mission export (JSON)

## State Management

### Zustand Stores

```typescript
// Auth store (persisted)
useAuthStore((state) => state.user)
useAuthStore((state) => state.login)

// UI store
useUIStore((state) => state.sidebarOpen)
useUIStore((state) => state.addToast)

// Selection store
useSelectionStore((state) => state.selectedModule)
useSelectionStore((state) => state.comparisonItems)
```

### React Query

```typescript
import { useSites, useDefects, useDashboardStats } from '@/hooks/useQueries';

const { data: sites } = useSites();
const { data: defects } = useDefects({ severity: 'critical' });
const { data: stats } = useDashboardStats();
```

## API Client

```typescript
import { apiClient } from '@/services/api';

// Login
await apiClient.login('email@example.com', 'password');

// Get sites
const sites = await apiClient.getSites();

// Get module telemetry
const telemetry = await apiClient.getModuleTelemetry('mod_001', 30);
```

## Environment Variables

Create `.env` file:

```bash
# Mapbox (required for maps)
VITE_MAPBOX_TOKEN=pk.your_token_here

# API (optional, defaults to proxy)
VITE_API_URL=http://localhost:8000/api/v1
```

## Design Tokens

### Colors

```javascript
// Primary (Solar theme)
primary-500: #f59e0b  // Solar yellow

// Secondary (Professional)
secondary-500: #3b82f6  // Blue

// Severity
severity-low: #22c55e
severity-medium: #f59e0b
severity-high: #f97316
severity-critical: #ef4444

// Thermal palette
thermal-cold: #0000ff
thermal-cool: #00ffff
thermal-neutral: #00ff00
thermal-warm: #ffff00
thermal-hot: #ff0000
```

## Component Examples

### StatCard

```tsx
<StatCard
  title="Total Sites"
  value={42}
  icon="📍"
  trend="+2 this month"
  trendUp={true}
/>
```

### ThermalViewer

```tsx
<ThermalViewer
  moduleId="mod_001"
  colorPalette="ironbow"
  showTemperatureScale={true}
/>
```

## Testing

### Unit Tests

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent prop="value" />);
    expect(screen.getByText('Expected')).toBeInTheDocument();
  });
});
```

### E2E Tests

```typescript
import { test, expect } from '@playwright/test';

test('should login successfully', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'admin@doctor-doom.com');
  await page.fill('[name="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/');
});
```

## Performance Optimization

- Code splitting by route
- Deck.gl layer memoization
- Virtual scrolling for large tables
- Image lazy loading
- React Query caching

## Browser Support

- Chrome 120+
- Firefox 120+
- Safari 17+
- Edge 120+

## License

Proprietary - All rights reserved
