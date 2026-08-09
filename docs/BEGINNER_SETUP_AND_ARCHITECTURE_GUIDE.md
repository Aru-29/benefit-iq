# Benefit IQ: Beginner Setup, Business Domain & Architecture Guide

Welcome to **Benefit IQ**, an enterprise healthcare benefit utilization analytics and administrative platform.

---

## 1. Line-by-Line Beginner Setup Guide

Follow these exact commands to run the platform from scratch.

### Step 1: Clone & Navigate to Project Workspace
```bash
cd D:\Projects\benefit-iq
```

### Step 2: Set Up Backend Python Environment
```bash
# Navigate to backend directory
cd benefit-iq-be

# Create virtual environment (if not created)
python -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
```

### Step 3: Start Infrastructure via Docker Compose
```bash
# Start ClickHouse, Redis, OpenBao Vault, Kafka, and OpenTelemetry Collector
docker compose up -d

# Check that all 5 containers are running
docker ps
```

### Step 4: Seed Database & Secrets
```bash
# Seed ClickHouse database schema & default records
docker exec -i clickhouse_db clickhouse-client --multiquery < scripts/init_clickhouse.sql

# Seed initial OpenBao Vault secrets (using env variable, NO hardcoded root tokens)
$env:BAO_TOKEN="root"
curl --header "X-Vault-Token: $env:BAO_TOKEN" --request POST --data '{"data": {"secret_value": "change-me-in-production"}}' http://127.0.0.1:8200/v1/secret/data/benefit-iq-be/jwt_secret_key
curl --header "X-Vault-Token: $env:BAO_TOKEN" --request POST --data '{"data": {"secret_value": "smtp-secret-password"}}' http://127.0.0.1:8200/v1/secret/data/benefit-iq-be/smtp_password
```

### Step 5: Start Backend FastAPI Application
```bash
# Run uvicorn server on port 8080
$env:PYTHONPATH="src"
python -m uvicorn benefit_iq.main:app --reload --host 127.0.0.1 --port 8080
```

### Step 6: Start Frontend Angular Application (New Terminal)
```bash
# Navigate to frontend directory
cd D:\Projects\benefit-iq\benefit-iq-fe

# Install npm packages
npm install

# Start Angular development server
npm start
```

Open your browser at `http://localhost:4200` to interact with Benefit IQ!

---

## 2. API Endpoints Reference

### Authentication & Identity (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Initial user registration and OTP email generation.
- `POST /api/v1/auth/verify-registration-otp` — Verifies registration OTP and returns `access_token` and `refresh_token`.
- `POST /api/v1/auth/login` — Account login, RSA password decryption, and OTP generation.
- `POST /api/v1/auth/verify-login-otp` — Verifies login OTP and returns session tokens.
- `POST /api/v1/auth/refresh` — Rotates refresh token to obtain a new access token.
- `POST /api/v1/auth/logout` — Revokes current user session.
- `GET /api/v1/auth/me` — Returns authenticated user profile and role details.

### Users & Administration (`/api/v1/users`)
- `GET /api/v1/users/me` — Retrieves current user profile.
- `POST /api/v1/users/query` — Datatype-aware generic user filtering, sorting, and pagination.
- `GET /api/v1/users/lookup` — Generic user lookup endpoint for UI autocompletes (`GET /users/lookup?search=admin&page=1&page_size=20`).

### Roles & RBAC (`/api/v1/roles`)
- `GET /api/v1/roles` — Lists system access control roles.
- `GET /api/v1/roles/lookup` — Generic role lookup for UI autocompletes (`GET /roles/lookup?search=admin`).
- `POST /api/v1/roles` — Admin Only: Creates custom access role.

### Analytics & Utilization (`/api/v1/analytics`)
- `GET /api/v1/analytics/kpi` — Retrieves top-level benefit utilization KPI metrics.
- `GET /api/v1/analytics/utilization-trends` — Retrieves monthly claims timeline by category.
- `GET /api/v1/analytics/category-breakdown` — Category percentage breakdown.

### OpenBao Vault Secrets Proxy (`/api/v1/secrets`)
- `GET /api/v1/secrets` — Admin Only: Lists secret paths and masked status (Secrets are NEVER exposed to FE directly).
- `POST /api/v1/secrets/value` — Admin Only: Writes a key-value secret to OpenBao.
- `POST /api/v1/secrets/rotate` — Admin Only: Rotates secret key.

---

## 3. Business Domain Rules

1. **Role-Based Access Control (RBAC)**:
   - `ADMIN`: Full access to user management, roles, configuration, OpenBao secrets proxy, system health, and audit logs.
   - `CUSTOMER`: Access restricted to Customer Utilization Analytics Dashboard (`/`) and personal account settings.
2. **Security & Cryptography**:
   - Client-side passwords are encrypted using **RSA-OAEP 2048-bit** public key before network transmission and decrypted server-side.
   - Passwords are stored in ClickHouse using **Argon2id** password hashing.
   - OTP codes are 6-digit alphanumeric strings hashed in Redis with strict 5-minute expiration windows.
3. **Secret Isolation**:
   - OpenBao Vault is never exposed directly to client scripts. All secret reads/writes pass through authorized backend API routes.

---

## 4. Request Cancellation Infrastructure

To prevent race conditions and unnecessary server load:

### Frontend RxJS Cancellation
- `GenericLookupComponent` uses `debounceTime(300)` and `switchMap()` operator.
- When a user types in a lookup search input, `switchMap` automatically **cancels any pending HTTP request** in flight before sending the new request.
- Route guards and component destruction use `takeUntilDestroyed()` to cancel pending subscriptions on navigation.

### Backend Async Cancellation
- FastAPI routers process requests as async tasks. If a client disconnects or cancels an HTTP request, Python raises `asyncio.CancelledError`, allowing resources to be freed immediately.

---

## 5. Architectural DOs and DON'Ts

### DOs:
- **DO** use generic lookup components (`GenericLookupComponent<T>`) for dropdowns instead of loading thousands of records into browser memory.
- **DO** keep secrets in OpenBao Vault and load them dynamically using environment tokens (`OPENBAO_TOKEN`).
- **DO** use HSL color tokens, glassmorphism depth, and fluid typography (`clamp()`) in custom CSS (`styles.css`).
- **DO** ensure all API inputs are validated using Pydantic schemas.

### DON'Ts:
- **DON'T** hardcode secrets or `"root"` tokens in code files or git repositories.
- **DON'T** expose OpenBao Vault endpoints directly to frontend scripts.
- **DON'T** use Tailwind or Bootstrap utility classes; stick to the custom CSS design system.
- **DON'T** fetch entire database tables to filter records client-side; always use server-side pagination and filtering (`POST /query` or `GET /lookup`).
