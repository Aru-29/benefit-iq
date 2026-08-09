# Benefit IQ Backend Service (`benefit-iq-be`)

FastAPI enterprise backend for Benefit IQ providing authentication, generic parameterized query & lookup infrastructure, ClickHouse persistence, Redis caching, OpenBao Vault proxy, and OpenTelemetry instrumentation.

## Quick Start
```bash
# 1. Start Infrastructure
docker compose up -d

# 2. Seed Database Schema & Data
docker exec -i clickhouse_db clickhouse-client --multiquery < scripts/init_clickhouse.sql

# 3. Start API Server (Port 8080)
$env:PYTHONPATH="src"
python -m uvicorn benefit_iq.main:app --reload --host 127.0.0.1 --port 8080
```

## Documentation
- 📖 [Beginner Setup & Architecture Guide](../docs/BEGINNER_SETUP_AND_ARCHITECTURE_GUIDE.md)
- 🛠️ [Disaster Recovery & Data Bootstrapping Guide](../docs/RECOVERY_AND_DATA_BOOTSTRAPPING.md)