"""
Module missing docstring.
"""

import json
from typing import Any

import structlog
from confluent_kafka import Producer

from benefit_iq.infrastructure.utils.retry import with_retry

logger = structlog.get_logger(__name__)


class KafkaProducerService:
    """Asynchronous Kafka Producer utilizing a thread-pool via run_in_executor to avoid blocking the event loop."""

    def __init__(self, bootstrap_servers: str) -> None:
        """Function missing docstring."""
        self.bootstrap_servers = bootstrap_servers
        self.producer = Producer(
            {
                "bootstrap.servers": self.bootstrap_servers,
                "message.send.max.retries": 5,
                "retry.backoff.ms": 500,
            }
        )

    def _delivery_report(self, err: Any, msg: Any) -> None:
        """Function missing docstring."""
        if err is not None:
            logger.error("kafka_message_delivery_failed", error=str(err), topic=msg.topic())
        else:
            logger.debug(
                "kafka_message_delivered",
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset(),
            )

    def publish_sync(self, topic: str, message: dict[str, Any], key: str | None = None) -> None:
        """Publishes a message synchronously. Usually called via run_in_executor."""
        value = json.dumps(message).encode("utf-8")
        key_bytes = key.encode("utf-8") if key else None
        self.producer.produce(topic, key=key_bytes, value=value, callback=self._delivery_report)
        self.producer.poll(0)

    async def publish(self, topic: str, message: dict[str, Any], key: str | None = None) -> None:
        """Asynchronously publish a message."""
        import asyncio

        loop = asyncio.get_running_loop()

        async def do_publish() -> None:
            """Async function missing docstring."""
            await loop.run_in_executor(None, self.publish_sync, topic, message, key)

        await with_retry(
            operation=do_publish, max_attempts=3, operation_name=f"kafka_publish_{topic}"
        )

    def flush(self) -> None:
        """Flushes the producer. Call during shutdown."""
        self.producer.flush(10.0)
