# Benefit IQ - DeepWiki & Architecture Flow

This document provides a comprehensive overview of the Benefit IQ project, detailing its execution flow, architecture, current capabilities, and suggestions for future enhancements in both the Frontend (Angular) and Backend (FastAPI).

## 1. Execution Flow & Architecture

### Frontend (Angular)
The frontend is an Angular 18+ application utilizing standalone components, `@ngrx/signals` for state management, and modern CSS features (variables, grid/flex layouts).

**Execution Path:**
1.  **`main.ts`**: The entry point of the application. It bootstraps the `AppComponent` using `appConfig`.
2.  **`app.config.ts`**: Configures the dependency injection container for the app. It provides:
    *   Routing configuration from `app.routes.ts`.
    *   HTTP Interceptors (`AuthInterceptor`, `ErrorInterceptor`) for token injection and centralized error handling.
    *   Social Login configurations (Google, Microsoft).
    *   Animations module.
3.  **`app.component.ts`**: The root component. It contains the `<router-outlet>` where all other route components are rendered.
4.  **`app.routes.ts`**: Defines the application routing table.
    *   `/auth`: Lazy loads auth routes (`login`, `register`, `otp-verify`, `sso-callback`).
    *   `/admin`: Protected admin area, lazy loads admin routes (`dashboard`, `users`, `config`). Guarded by Auth and Role guards.
    *   `/customer`: Protected customer area, lazy loads customer routes (`dashboard`). Guarded by Auth guard.
5.  **State Management (`AuthStore`)**: Uses `@ngrx/signals` in `auth.store.ts` to hold the current user session, roles, and authentication status. It is injected across components to verify access.

### Backend (FastAPI)
The backend is a high-performance Python FastAPI application designed using Clean Architecture and CQRS principles.

**Execution Path:**
1.  **`main.py`**: The entry point. Imports and runs the `app` instance.
2.  **`bootstrap.py`**: Contains `create_application()`, which:
    *   Initializes settings and structured logging (Structlog).
    *   Wires the Dependency Injection container (`dependency_injector`).
    *   Adds Middlewares (CORS, Rate Limiting via Redis, Correlation IDs, Request Logging).
    *   Registers Exception Handlers mapping domain exceptions to HTTP responses.
    *   Includes all API `routers/v1/` endpoints.
    *   Manages lifecycle events (connecting to ClickHouse database and Redis).
3.  **Routers (`api/routers/v1/`)**: Define the endpoints (`auth`, `users`, `analytics`, `config`, `roles`, etc.). They inject required services (from `dependencies`) to process requests.
4.  **Application / Domain / Infrastructure Layers**:
    *   **API**: Controllers (Routers), Middlewares, Schemas.
    *   **Application**: Contracts and Use Cases.
    *   **Domain**: Core business logic, Entities, Exceptions, Value Objects.
    *   **Infrastructure**: Database access (ClickHouse, Redis), Email, Security (Argon2id, JWT), ML, Telemetry.

---

## 2. Current Routes, Pages, and Functionalities

### Frontend Pages
*   **Auth Module**
    *   `/auth/login`: Standard email/password login and SSO entry points (Google/Microsoft).
    *   `/auth/register`: User registration with password strength indication.
    *   `/auth/otp-verify`: Handles 2FA / Email Verification via 6-digit OTP.
    *   `/auth/callback`: Handles OAuth redirect processing and token exchange.
*   **Customer Module**
    *   `/customer/dashboard`: Main user view to track credit cards, benefit utilizations, remaining values, record usage, and view smart recommendations.
*   **Admin Module**
    *   `/admin`: Dashboard with high-level KPIs, system health (Redis stats), and recent users.
    *   `/admin/users`: Data table view for managing users.
    *   `/admin/config`: Data table view for application configuration management.
*   **Shared / UI**
    *   **Chatbot**: A floating AI assistant widget for context-aware help.
    *   **DataTable**: Reusable material table with sorting and filtering.
    *   **PasswordInput**: Custom input with visibility toggle and strength meter.

### Backend Functionalities
*   **Authentication & Security**: Argon2id hashing, stateful Redis refresh token rotation, JWT access tokens, Google/Microsoft OAuth2 integration.
*   **Analytics Engine**: ClickHouse `ReplacingMergeTree` powered analytics for high-volume telemetry and usage calculation.
*   **Role-Based Access Control (RBAC)**: Fine-grained permissions checking at endpoint boundaries.
*   **Observability**: OpenTelemetry tracing, Prometheus metrics, and structured JSON logs.

---

## 3. Future Implementation Suggestions

1.  **Backend Caching Layer Optimization**: 
    *   Implement layered caching using Redis for frequently accessed configuration and user profiles to reduce database load.
2.  **Notification System**: 
    *   Add an in-app notification center via WebSockets or Server-Sent Events (SSE) to alert users when a benefit is about to expire or when new benefits are unlocked.
3.  **Enhanced ML Recommendations**: 
    *   Integrate a real-time recommendation engine in the backend `ml` layer that analyzes transaction history to suggest the most optimal card for a specific merchant.
4.  **Data Export & Reporting**: 
    *   Allow administrators to export data tables to CSV/Excel from the frontend.
    *   Generate automated monthly benefit statements for users via PDF generation in the backend.
5.  **Multi-Language Support (i18n)**:
    *   Implement Angular `@angular/localize` to support multiple languages, starting with English, Spanish, and French.

---

## 4. Design Suggestions (UI/UX)

1.  **Dark Mode Integration**:
    *   The current design relies heavily on light backgrounds. Introducing a native CSS variables-based dark mode toggle will improve accessibility and premium feel.
2.  **Micro-Interactions**:
    *   Add subtle hover animations on the benefit cards on the Customer Dashboard.
    *   Include skeleton loaders during API fetch states instead of simple "Loading..." text to reduce perceived latency.
3.  **Advanced Data Visualization**:
    *   Replace plain numbers in the Admin Dashboard with `Chart.js` (already in `package.json`) charts showing utilization trends over time and active user growth.
4.  **Responsive Polish**:
    *   Ensure the `DataTableComponent` stacks gracefully on mobile screens, as wide tables currently require horizontal scrolling which can be clumsy on small devices.
5.  **Empty States**:
    *   Design beautiful empty states with illustrations (e.g., when a user has no cards added yet) that guide them directly to the primary action ("Add a Card").
