# Frontend & Mobile Squad Tasks

## Phase 1: Setup & Design (Week 1)
- [ ] **Project Initialization**
    - [ ] Setup Next.js 14 (App Router) with TypeScript & Tailwind CSS.
    - [ ] Configure ESLint, Prettier, and Husky hooks.
- [ ] **Component Library (ShadCN/UI)**
    - [ ] Implement accessible standard components (Buttons, Inputs, Cards).
    - [ ] Create mobile-first Layout (Bottom navigation for mobile web).

## Phase 2: Core Features (Week 2)
- [ ] **Dashboard Implementation**
    - [ ] **Mandi Map:** Integrate Leaflet/Mapbox to show nearby mandis.
    - [ ] **Price Charts:** Use Recharts to visualize historic vs predicted prices.
    - [ ] **Commodity Selector:** Auto-complete search for crops.
- [ ] **API Integration**
    - [ ] Create React Query hooks for fetching forecasts (`useForecast`).
    - [ ] Handle loading states and error boundaries gracefully.

## Phase 3: "Winning Features" (Week 3)
- [ ] **Voice Interface (The Differentiator)**
    - [ ] Implement "Mic Button" component.
    - [ ] Capture audio blob and send to Bhashini/Backend ASR endpoint.
    - [ ] Play back audio response (TTS).
- [ ] **Localization (i18n)**
    - [ ] Support English and Hindi UI labels.
    - [ ] Implement dynamic unit conversion (Quintal vs Kg).

## Phase 4: Polish (Week 4)
- [ ] PWA (Progressive Web App) manifest for "Install to Home Screen".
- [ ] Dark Mode support (high contrast for outdoor usage).
- [ ] Accessibility Audit (Lighthouse score 100).
