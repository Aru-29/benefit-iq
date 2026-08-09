# Walkthrough: Clean Compression & Restore Instructions

Cleaned up all temporary virtual environments and build cache directories (`.venv`, `node_modules`, `.angular`, `.pytest_cache`).

## Native Lockfiles & Re-installation Commands

### 1. Backend Setup (`benefit-iq-be`) using `uv`
Since the backend utilizes `uv` (`pyproject.toml` + `uv.lock`), restoring dependencies takes seconds:
```powershell
cd benefit-iq-be
uv sync
uv run uvicorn benefit_iq.main:app --reload --host 127.0.0.1 --port 8080
```

### 2. Frontend Setup (`benefit-iq-fe`) using `npm`
```powershell
cd benefit-iq-fe
npm install
npm start
```
