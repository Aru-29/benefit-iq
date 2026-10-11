# BenefitIQ setup guide

## Prerequisites

- Git, Docker Desktop with Compose, Node.js 20+ and npm.
- Python 3.14 with `venv` support. The backend currently declares Python 3.14 as its minimum version.
- Optional: `uv` for dependency management and an OpenBao instance for administrative secret storage.

## Clone and configure

```powershell
git clone <repository-url> benefit-iq
Set-Location benefit-iq
Copy-Item benefit-iq-be\.env.example benefit-iq-be\.env
```

Edit `benefit-iq-be\.env` for your machine. Do not commit it. Required local values are shown below; choose your own passwords and JWT secret outside local development.

```dotenv
APP_ENV=development
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=18123
CLICKHOUSE_DATABASE=benefitiq
CLICKHOUSE_USERNAME=default
CLICKHOUSE_PASSWORD=<local-compose-password>
REDIS_HOST=localhost
REDIS_PORT=16379
SMTP_HOST=localhost
SMTP_PORT=11025
SMTP_FROM_ADDRESS=noreply@benefitiq.local
OTEL_ENABLED=false
JWT_SECRET_KEY=<development-secret-at-least-32-characters>
INIT_ADMIN_EMAIL=<local-admin-email>
INIT_ADMIN_PASSWORD=<strong-local-password>
```

`OPENBAO_URL` and `OPENBAO_TOKEN` are optional for the local member workflow. Production startup requires an OpenBao token, database and Redis credentials, a non-default bootstrap administrator password, and `SECURITY_ENCRYPTION_PRIVATE_KEY_PATH` pointing to a persistent private key.

## Start local services

```powershell
docker compose -f compose.local.yml up -d
docker compose -f compose.local.yml ps
```

This starts ClickHouse on `localhost:18123`, Redis on `localhost:16379`, SMTP on `localhost:11025` and Mailpit at `http://localhost:18025`. The compose file is isolated from production and its development password must never be reused.

## Install and run the backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".\benefit-iq-be[ml]" pytest pytest-asyncio pytest-httpx ruff
$env:CLICKHOUSE_PORT = "18123"
$env:CLICKHOUSE_PASSWORD = "<local-compose-password>"
$env:REDIS_PORT = "16379"
$env:SMTP_PORT = "11025"
$env:OTEL_ENABLED = "false"
uvicorn benefit_iq.main:app --app-dir benefit-iq-be\src --reload --port 8080
```

The schema initializer runs at API startup. There is no separate migration framework yet. To create synthetic local records after the API dependencies are available, run:

```powershell
$env:BENEFITIQ_DEMO_PASSWORD = "<local-demo-password>"
python benefit-iq-be\scripts\seed_demo.py
```

The seed script is intentionally blocked outside `APP_ENV=development`.

## Install and run the frontend

In a second terminal:

```powershell
Set-Location benefit-iq-fe
npm ci
npm start
```

Open `http://localhost:4200`. The Angular proxy sends `/api` traffic to the backend. Mailpit displays local OTP messages at `http://localhost:18025`.

## Verify

```powershell
# Repository root
.\.venv\Scripts\python.exe -m ruff check benefit-iq-be
$env:RUN_INTEGRATION = "1"
$env:CLICKHOUSE_PORT = "18123"
$env:CLICKHOUSE_PASSWORD = "<local-compose-password>"
$env:REDIS_PORT = "16379"
$env:SMTP_PORT = "11025"
.\.venv\Scripts\python.exe -m pytest benefit-iq-be\tests -q

# Frontend directory
npm run build
npm test
```

## Troubleshooting

| Symptom | Resolution |
|---|---|
| Backend cannot connect to ClickHouse or Redis | Confirm `docker compose -f compose.local.yml ps` and align `.env` ports with the commands above. |
| No OTP appears | Check Mailpit, SMTP host/port and the backend logs. |
| Login encryption fails after restart | Set `SECURITY_ENCRYPTION_PRIVATE_KEY_PATH` to a persistent PEM key. Development may generate a process-local key. |
| Application rejects production configuration | Supply all production-required credentials and disable debug mode; do not suppress the validation. |
| Python executable reports a missing real location | Reinstall the Python version used to create `.venv`, delete only the local virtual environment, recreate it, then reinstall dependencies. |
| Frontend API calls fail | Start the FastAPI server on port 8080 and use `npm start` so Angular applies `proxy.conf.json`. |

Stop local services when finished with `docker compose -f compose.local.yml down`. Add `-v` only when you intentionally want to discard all local database data.
