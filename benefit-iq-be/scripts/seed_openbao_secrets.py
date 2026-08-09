"""Script to populate initial default secret paths into OpenBao / Vault.

Usage:
    python scripts/seed_openbao_secrets.py
"""
import asyncio
import os
import sys

# Ensure src/ is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from benefit_iq.infrastructure.secrets.openbao_manager import OpenBaoManager


async def seed_secrets():
    bao_url = os.getenv("OPENBAO_URL", "http://127.0.0.1:8200")
    bao_token = os.getenv("OPENBAO_TOKEN", "root")

    print(f"Connecting to OpenBao / Vault at {bao_url}...")
    manager = OpenBaoManager(bao_url=bao_url, bao_token=bao_token)

    secret_mappings = [
        ("secret/data/benefit-iq-be/jwt_secret_key", {"secret_value": "change-me-in-production"}),
        ("secret/data/benefit-iq-be/smtp_password", {"secret_value": "smtp_secret_pass"}),
        ("secret/data/benefit-iq-be/init_admin_password", {"secret_value": "Admin@123!"}),
        ("secret/data/benefit-iq-be/google_client_secret", {"secret_value": "google_client_secret_placeholder"}),
        ("secret/data/benefit-iq-be/microsoft_client_secret", {"secret_value": "microsoft_client_secret_placeholder"}),
        ("secret/data/benefit-iq-be/database_credentials", {"db_pass": "default_pass"}),
        ("secret/data/benefit-iq-be/redis_auth_token", {"token": "redis_auth_token_placeholder"}),
    ]

    for path, secrets in secret_mappings:
        try:
            await manager.set_secret(path, secrets)
            print(f"[SUCCESS] Seeded: {path} -> {list(secrets.keys())}")
        except Exception as e:
            print(f"[ERROR] Failed to seed {path}: {str(e)}")

    await manager.close()
    print("\nOpenBao secret seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_secrets())
