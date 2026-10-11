"""Infrastructure Health & Readiness Checker.

Performs explicit startup readiness and connectivity checks across ClickHouse,
Redis, OpenBao Vault, and Kafka, logging detailed operational status on app start.
"""

import socket
from typing import Any

import httpx
import structlog
from redis.asyncio import Redis

from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase
from benefit_iq.infrastructure.secrets.openbao_manager import OpenBaoManager

logger = structlog.get_logger(__name__)


class InfrastructureHealthChecker:
    """Startup health probe for core external infrastructure dependencies."""

    def __init__(
        self,
        clickhouse: ClickHouseDatabase,
        redis_client: Redis,
        openbao_manager: OpenBaoManager,
        kafka_host: str = "localhost",
        kafka_port: int = 9092,
    ) -> None:
        """Initialize health probe dependencies."""
        self.clickhouse = clickhouse
        self.redis = redis_client
        self.openbao = openbao_manager
        self.kafka_host = kafka_host
        self.kafka_port = kafka_port

    async def check_all(self) -> dict[str, Any]:
        """Executes health probe checks across all infrastructure dependencies."""
        logger.info("infrastructure_health_checks_started")

        results = {
            "clickhouse": await self.check_clickhouse(),
            "redis": await self.check_redis(),
            "openbao": await self.check_openbao(),
            "kafka": await self.check_kafka(),
        }

        all_healthy = all(status.get("status") == "HEALTHY" for status in results.values())
        if all_healthy:
            logger.info("infrastructure_health_checks_all_passed", details=results)
        else:
            logger.warning("infrastructure_health_checks_degraded", details=results)

        return results

    async def check_clickhouse(self) -> dict[str, Any]:
        """Probes ClickHouse database connectivity."""
        try:
            res = await self.clickhouse.query_async("SELECT 1")
            is_ok = bool(res and res.result_rows)
            return {
                "status": "HEALTHY" if is_ok else "UNHEALTHY",
                "details": "ClickHouse ping successful",
            }
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("clickhouse_health_check_failed", error=str(e))
            return {"status": "UNHEALTHY", "error": str(e)}

    async def check_redis(self) -> dict[str, Any]:
        """Probes Redis cache server connectivity using existing connected client."""
        try:
            client = getattr(self.redis, "client", self.redis)
            if client is not None and hasattr(client, "ping"):
                pong = await client.ping()
                is_ok = bool(pong)
                return {
                    "status": "HEALTHY" if is_ok else "UNHEALTHY",
                    "details": "Redis ping successful",
                }
            return {"status": "UNHEALTHY", "error": "Redis client not connected"}
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("redis_health_check_failed", error=str(e))
            return {"status": "UNHEALTHY", "error": str(e)}

    async def check_openbao(self) -> dict[str, Any]:
        """Probes OpenBao Vault health API."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.openbao.bao_url}/v1/sys/health")
                is_ok = res.status_code in (200, 429, 501, 503)
                return {
                    "status": "HEALTHY" if is_ok else "UNHEALTHY",
                    "status_code": res.status_code,
                    "details": "OpenBao Vault reachable",
                }
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("openbao_health_check_failed", error=str(e))
            return {"status": "UNHEALTHY", "error": str(e)}

    async def check_kafka(self) -> dict[str, Any]:
        """Probes Kafka broker TCP socket availability."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            result = sock.connect_ex((self.kafka_host, self.kafka_port))
            sock.close()
            is_ok = result == 0
            return {
                "status": "HEALTHY" if is_ok else "UNHEALTHY",
                "details": f"Kafka socket connect {self.kafka_host}:{self.kafka_port} success"
                if is_ok
                else "Socket connection refused",
            }
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("kafka_health_check_failed", error=str(e))
            return {"status": "UNHEALTHY", "error": str(e)}
