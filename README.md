# Benefit IQ: Enterprise Healthcare Benefit Utilization & Administrative Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/Aru-29/benefit-iq)
[![Python](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Angular](https://img.shields.io/badge/angular-19.0-red.svg)](https://angular.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Benefit IQ** is a production-grade enterprise platform designed for real-time healthcare benefit utilization analytics, dynamic key-value configuration management, OpenBao Vault secret management, RSA asymmetric encryption, and role-based access control (RBAC).

---

## 🌟 Architecture & Features Summary

### 1. Generic Parameterized Query & Lookup Engine
- **ClickHouse Query Builder**: Datatype-aware parameterized SQL builder supporting AND/OR filter groups, server-side sorting, pagination, and aggregate queries.
- **Generic Lookup Component (`GenericLookupComponent<T>`)**: Reusable Angular autocomplete with debounced search (`300ms`), cancellation of obsolete requests (`switchMap`), infinite scroll pagination, keyboard accessibility, and `LookupAdapter<T>` interface.

### 2. Customer Analytics Dashboard (Power BI / Tableau Style)
- **KPI Metrics**: Total Utilization, Approved Claims %, Cumulative Savings, Active Members, Loss Ratio.
- **Interactive Visualizations**: Monthly Claims Timeline Chart & Coverage Category Share breakdown.
- **Data Export**: Export filtered utilization reports directly to CSV.

### 3. Administrative Management Portal
- **User Management**: Server-side generic query, search, filtering, and deactivation.
- **Role & RBAC Management**: System role management and generic lookup integration.
- **App Configuration**: Key-value configuration listing, value editor, and secret toggles.
- **OpenBao Secrets Proxy**: Vault secret metadata listing, key rotation, and secret writing strictly via authorized backend proxy APIs (never exposing OpenBao Vault directly to client scripts).
- **Crypto & Key Management**: RSA-OAEP 2048-bit asymmetric key pair management and PEM display.
- **System & Redis Health**: Real-time Redis memory, connected clients, total keys count, and cache flushing.
- **Audit Activity Log**: System administrative activity trail.

### 4. AI Assistant Chatbot Widget
- Floating conversational AI widget with typing indicators, suggested prompt chips, message history, retry, and clear actions.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python** 3.11+
- **Node.js** 20+ & **npm** 10+
- **Docker Desktop** & **Docker Compose**

### 1. Infrastructure Setup (Docker Compose)
```bash
cd benefit-iq-be

# Spin up ClickHouse, Redis, OpenBao Vault, Kafka, and OpenTelemetry Collector
docker compose up -d

# Verify all containers are UP
docker ps
```

### 2. Initialize Database & Secrets
```bash
# Seed ClickHouse database schema & tables
docker exec -i clickhouse_db clickhouse-client --multiquery < scripts/init_clickhouse.sql

# Seed initial OpenBao Vault secrets (Using environment variable, NO hardcoded root tokens)
$env:BAO_TOKEN="root"
curl --header "X-Vault-Token: $env:BAO_TOKEN" --request POST --data '{"data": {"secret_value": "change-me-in-production"}}' http://127.0.0.1:8200/v1/secret/data/benefit-iq-be/jwt_secret_key
```

### 3. Backend Setup & Server Start
```bash
cd benefit-iq-be
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:PYTHONPATH="src"
python -m uvicorn benefit_iq.main:app --reload --host 127.0.0.1 --port 8080
```

### 4. Frontend Setup & Application Start
```bash
cd benefit-iq-fe
npm install
npm start
```
Navigate to `http://localhost:4200` in your web browser.

---

## 📚 Technical Documentation

Comprehensive setup, disaster recovery, and architecture guides are available in the [`docs/`](docs/) directory:

- 📖 [Beginner Setup & Architecture Guide](docs/BEGINNER_SETUP_AND_ARCHITECTURE_GUIDE.md) — Detailed line-by-line setup, complete API endpoint catalog, business domain rules, RxJS/Asyncio cancellation mechanics, and architectural DOs and DON'Ts.
- 🛠️ [Disaster Recovery & Data Bootstrapping Guide](docs/RECOVERY_AND_DATA_BOOTSTRAPPING.md) — Step-by-step instructions for recovering from wiped Docker volumes, re-populating ClickHouse tables, writing OpenBao secrets, and initializing Kafka topics.

---

## 🧪 Testing

### Backend Unit Tests
```bash
cd benefit-iq-be
$env:PYTHONPATH="src"
python -m pytest tests/unit/
```

### Frontend Build Verification
```bash
cd benefit-iq-fe
npm run build
```

---

## 🛡️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
