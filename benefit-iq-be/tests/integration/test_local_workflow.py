"""Runs only against explicitly enabled isolated local services."""

import importlib.util
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_INTEGRATION") != "1",
    reason="Set RUN_INTEGRATION=1 with local Compose running",
)


def test_authenticated_workflow():
    from benefit_iq.bootstrap import create_application

    spec = importlib.util.spec_from_file_location(
        "seed_demo", Path(__file__).parents[2] / "scripts/seed_demo.py"
    )
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    app = create_application()
    with TestClient(app) as client:
        customer_id, product_id = client.portal.call(seed.seed, app.container)
        assert client.get("/api/v1/health/ready").status_code == 200
        assert client.get("/api/v1/analytics/me/cards").status_code in (401, 403)
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "customer@example.com",
                "password": os.environ["BENEFITIQ_DEMO_PASSWORD"],
            },
        )
        assert response.status_code == 200, response.text
        messages = httpx.get("http://127.0.0.1:18025/api/v1/messages").json()["messages"]
        message = httpx.get("http://127.0.0.1:18025/api/v1/message/" + messages[0]["ID"]).json()
        otp = re.search(r"\b[0-9]{6}\b", message["HTML"] or message["Text"]).group()
        response = client.post(
            "/api/v1/auth/verify-login-otp", json={"email": "customer@example.com", "otp": otp}
        )
        assert response.status_code == 200, response.text
        tokens = response.json()["data"]
        client.headers["Authorization"] = "Bearer " + tokens["access_token"]
        card = client.post(
            "/api/v1/analytics/me/cards",
            json={
                "product_id": str(product_id),
                "last_four": str(uuid4().int % 10000).zfill(4),
                "alias": "Test card",
            },
        )
        assert card.status_code == 201, card.text
        card_id = card.json()["data"]["id"]
        assert (
            client.get(f"/api/v1/analytics/customers/{seed.uid('other')}/utilization").status_code
            == 403
        )
        assert client.get("/api/v1/analytics/kpi").status_code == 403
        summary = client.get("/api/v1/analytics/me/utilization")
        assert summary.status_code == 200, summary.text
        benefits = [b for b in summary.json()["data"]["utilizations"] if b["card_id"] == card_id]
        assert len(benefits) == 4
        travel = next(b for b in benefits if b["benefit_category"] == "travel_credit")
        assert float(travel["entitled_value"]) == 200
        body = {
            "external_id": str(uuid4()),
            "card_id": card_id,
            "benefit_id": travel["benefit_id"],
            "value": "12.34",
            "currency": "USD",
        }
        first = client.post("/api/v1/analytics/me/usage", json=body)
        assert first.status_code == 201, first.text
        second = client.post("/api/v1/analytics/me/usage", json=body)
        assert first.json()["data"]["id"] == second.json()["data"]["id"]
        assert (
            client.post("/api/v1/analytics/me/usage", json={**body, "value": "13"}).status_code
            == 422
        )
        body["card_id"] = str(uuid4())
        assert client.post("/api/v1/analytics/me/usage", json=body).status_code == 404
        tx = {
            "external_id": str(uuid4()),
            "card_id": card_id,
            "amount": "23.45",
            "currency": "USD",
            "merchant_name": "Demo",
            "merchant_category_code": "5812",
            "transaction_date": datetime.now(UTC).isoformat(),
        }
        first = client.post("/api/v1/analytics/me/transactions", json=tx)
        assert first.status_code == 201, first.text
        second = client.post("/api/v1/analytics/me/transactions", json=tx)
        assert second.json()["data"]["id"] == first.json()["data"]["id"]
        assert (
            client.post(
                "/api/v1/analytics/me/transactions", json={**tx, "amount": "99"}
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/analytics/me/transactions/" + first.json()["data"]["id"] + "/reverse"
            ).status_code
            == 200
        )
        assert client.get("/api/v1/analytics/me/recommendations").status_code == 200
        rotated = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert rotated.status_code == 200, rotated.text
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
            ).status_code
            != 200
        )
        assert client.get("/api/v1/analytics/me/cards").status_code == 401
