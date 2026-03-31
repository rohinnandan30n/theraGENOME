"""
Kafka producer for emitting processed drug safety results.
"""
import json
import logging
from aiokafka import AIOKafkaProducer
from typing import Optional
from src.config import settings

logger = logging.getLogger(__name__)

_kafka_producer: Optional[AIOKafkaProducer] = None


async def get_kafka_producer() -> AIOKafkaProducer:
    """Get or create Kafka producer."""
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await _kafka_producer.start()
        logger.info("Kafka producer started")
    return _kafka_producer


async def emit_drug_safety_result(
    patient_id: str,
    drug_name: str,
    toxicity_score: float,
    pgx_results: dict,
    ddi_warnings: list,
):
    """Emit processed drug safety result to Kafka topic (for logging/audit)."""
    try:
        producer = await get_kafka_producer()

        message = {
            "patient_id": patient_id,
            "drug_name": drug_name,
            "toxicity_score": toxicity_score,
            "pgx_results": pgx_results,
            "ddi_warnings": ddi_warnings,
        }

        await producer.send_and_wait(
            "drug_safety_results",
            value=message,
        )

        logger.info(f"Emitted drug safety result for patient {patient_id}: {drug_name}")

    except Exception as e:
        logger.error(f"Error emitting drug safety result: {e}")


async def close_kafka_producer():
    """Close Kafka producer."""
    global _kafka_producer
    if _kafka_producer:
        await _kafka_producer.stop()
        logger.info("Kafka producer stopped")
