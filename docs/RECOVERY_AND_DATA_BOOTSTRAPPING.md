# Benefit IQ: Infrastructure Disaster Recovery & Data Bootstrapping Guide

This document provides a beginner-friendly, step-by-step guide to recovering the entire Benefit IQ infrastructure and re-populating data if your Docker containers, volumes, or databases are cleared or wiped (`docker compose down -v`).

---

## 1. Quick Emergency Recovery Checklist

When your Docker containers or volumes are wiped, follow these steps in order:

```bash
# Step 1: Navigate to backend folder
cd benefit-iq-be

# Step 2: Remove any leftover orphaned containers and network conflicts
docker compose down --remove-orphans

# Step 3: Spin up clean infrastructure containers
docker compose up -d

# Step 4: Verify all 5 containers are UP and healthy
docker ps
```

---

## 2. Populating ClickHouse Database Tables & Seed Data

If ClickHouse volumes were deleted, run the SQL initialization script `scripts/init_clickhouse.sql`.

### Option A: Using `clickhouse-client` inside Docker
```bash
docker exec -i clickhouse_db clickhouse-client --multiquery < scripts/init_clickhouse.sql
```

### Option B: Using Curl HTTP Interface
```bash
curl -X POST "http://localhost:8123/?query=CREATE%20DATABASE%20IF%20NOT%20EXISTS%20benefitiq"
curl --data-binary @scripts/init_clickhouse.sql "http://localhost:8123/"
```

### Verification
Run this query to verify tables were populated:
```bash
curl "http://localhost:8123/?query=SHOW%20TABLES%20FROM%20benefitiq"
```

---

## 3. Populating OpenBao Vault Secrets (Security Best Practices)

> [!IMPORTANT]
> Never hardcode root tokens or secrets directly in application code. Use environment variables (`OPENBAO_TOKEN`).

### Step-by-Step OpenBao Secret Seeding:

#### 1. Export OpenBao Address and Vault Token:
```bash
# PowerShell (Windows)
$env:BAO_ADDR="http://127.0.0.1:8200"
$env:BAO_TOKEN="root"  # Replace with production vault token in staging/prod

# Linux / macOS
export BAO_ADDR="http://127.0.0.1:8200"
export BAO_TOKEN="root"
```

#### 2. Seed Secret Key-Value Pairs into OpenBao:
```bash
# Write JWT Signing Secret
curl --header "X-Vault-Token: $env:BAO_TOKEN" \
     --request POST \
     --data '{"data": {"secret_value": "your-secure-jwt-secret-key-32chars+"}}' \
     http://127.0.0.1:8200/v1/secret/data/benefit-iq-be/jwt_secret_key

# Write SMTP Email Password
curl --header "X-Vault-Token: $env:BAO_TOKEN" \
     --request POST \
     --data '{"data": {"secret_value": "smtp-app-password-here"}}' \
     http://127.0.0.1:8200/v1/secret/data/benefit-iq-be/smtp_password

# Write Initial Admin Password
curl --header "X-Vault-Token: $env:BAO_TOKEN" \
     --request POST \
     --data '{"data": {"secret_value": "Admin@123!"}}' \
     http://127.0.0.1:8200/v1/secret/data/benefit-iq-be/init_admin_password
```

#### 3. Verify Secret Value in OpenBao:
```bash
curl --header "X-Vault-Token: $env:BAO_TOKEN" \
     http://127.0.0.1:8200/v1/secret/data/benefit-iq-be/jwt_secret_key
```

---

## 4. Bootstrapping Apache Kafka Topics

When Kafka starts up clean, create the default application event topics:

```bash
# Create user events topic
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --create --topic benefit-iq.user-events --partitions 3 --replication-factor 1

# Create audit logs topic
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --create --topic benefit-iq.audit-logs --partitions 3 --replication-factor 1

# List active Kafka topics
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
```

---

## 5. Troubleshooting & Verification

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `Bind for 0.0.0.0:9092 failed` | Port 9092 bound by legacy container | Run `docker stop local-kafka` or `docker compose down --remove-orphans` |
| `OpenBao GET 404 Not Found` | Secret key not written to OpenBao Vault | Run Section 3 curl script to seed secret values |
| `Connection refused 4317` | OpenTelemetry collector down | Verify `otel-collector` container in `docker ps` |
