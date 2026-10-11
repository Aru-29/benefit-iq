# API reference

All routes are prefixed with `/api/v1`. Responses use `{ "success": true, "data": ... }`; validation failures use standard FastAPI error responses. Except for health and authentication bootstrap routes, a Bearer access token is required.

## Health and authentication

| Method | Route | Description |
|---|---|---|
| GET | `/health/live` | Process liveness only. |
| GET | `/health/ready` | Verifies ClickHouse and Redis connectivity. |
| GET | `/auth/public-key` | Returns the RSA public key used by the browser to encrypt password payloads. |
| POST | `/auth/register` | Creates a local account and sends registration verification. |
| POST | `/auth/verify-registration-otp` | Consumes a one-time registration OTP and issues access/refresh tokens. |
| POST | `/auth/login` | Validates encrypted credentials and sends a login OTP; no session is issued yet. |
| POST | `/auth/verify-login-otp` | Atomically consumes the login OTP and issues tokens. |
| POST | `/auth/refresh` | Atomically rotates a Redis-backed refresh token. |
| POST | `/auth/logout` | Revokes the submitted refresh token. |
| POST | `/auth/forgot-password`, `/auth/reset-password`, `/auth/change-password`, `/auth/verify-email` | Account recovery, password change and verification workflows. |
| POST | `/auth/{provider}/callback` | Exchanges a validated Google or Microsoft provider callback for application tokens. |

## Member benefit workflow

| Method | Route | Description |
|---|---|---|
| GET | `/analytics/cards`, `/analytics/benefits` | Reads the active product and benefit catalogue. |
| GET/POST | `/analytics/me/cards` | Lists the caller’s cards or links an active product using a deterministic idempotency key. |
| GET | `/analytics/me/utilization` | Calculates current-period entitlement, use and remaining value for the caller, scoped to one currency. |
| GET | `/analytics/me/transactions` | Lists caller-owned transactions with bounded pagination. |
| POST | `/analytics/me/transactions` | Ingests one posted transaction. The caller must own the card; duplicate external IDs are idempotent. |
| POST | `/analytics/me/transactions/{transaction_id}/reverse` | Reverses only a caller-owned transaction. |
| POST | `/analytics/me/usage` | Records a caller-owned redemption/use after entitlement and remaining-capacity checks. |
| GET/POST | `/analytics/me/nudges` | Lists reminders or generates period-idempotent benefit reminders. In-app delivery is immediate; email requires explicit member opt-in. |
| POST | `/analytics/me/nudges/{nudge_id}/status` | Lets the owning member mark a reminder opened or dismissed. |
| POST | `/analytics/me/enrollments` | Records a self-reported enrolment for a benefit linked to the member’s card. |
| GET | `/analytics/me/recommendations` | Returns deterministic opportunity-priority ordering, not an ML probability. |
| GET | `/analytics/me/redemption-predictions` | Returns trained-model probabilities only when a validated local model artifact is configured; otherwise returns `available: false`. |

`/analytics/customers/{customer_id}/utilization` is identity-checked and only permits the authenticated customer. `/analytics/kpi` is administrator-only.

## Administration

| Route family | Description |
|---|---|
| `/users/me` | Read or update the authenticated profile. |
| `/users`, `/users/{id}`, `/users/query`, `/users/lookup` | Administrator user management and constrained lookup/query functions. |
| `/roles` | Administrator role create, list, read, update and deactivate operations. |
| `/config` | Administrator configuration metadata and value management. Values marked secret must be stored through the managed secret store. |
| `/secrets` | Administrator-only metadata, write and rotation for an allow-listed set of OpenBao paths. |
| `/system/redis/stats` | Administrator operational Redis statistics. |
| `/crypto/*` | Authenticated encryption, decryption, encoding and hash utilities; application authentication uses the dedicated auth routes. |

## Safety rules

The server derives customer identity from the access token, uses UTC timestamps, represents cash with `Decimal`, keeps currencies separate, and treats benefit periods as `[start, end)`. Coverage and count benefits are not summed as cash. Administrative access is enforced by server-side role checks, not frontend routing.
