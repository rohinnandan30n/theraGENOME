"""
Kafka consumer for the omics_processed topic.
Listens for processed omics data from Dev 4 and triggers toxicity checks.
"""
import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from typing import Optional
from src.config import settings

logger = logging.getLogger(__name__)

_kafka_consumer: Optional[AIOKafkaConsumer] = None


async def start_kafka_consumer():
    """Start Kafka consumer in background."""
    global _kafka_consumer

    try:
        _kafka_consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_OMICS_PROCESSED,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="dev3-toxicity-service",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        await _kafka_consumer.start()
        logger.info(f"Kafka consumer started for topic: {settings.KAFKA_TOPIC_OMICS_PROCESSED}")

        # Run consumer in background task
        asyncio.create_task(_consume_messages())

    except Exception as e:
        logger.error(f"Failed to start Kafka consumer: {e}")
        _kafka_consumer = None


async def _consume_messages():
    """Consume messages from Kafka topic."""
    if not _kafka_consumer:
        return

    try:
        async for message in _kafka_consumer:
            await _handle_omics_message(message.value)
    except asyncio.CancelledError:
        logger.info("Kafka consumer cancelled")
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {e}")


async def _handle_omics_message(message: dict):
    """
    Handle omics_processed message from Dev 4.
    Expected message format: {patient_id, drug_list, gene_expression}
    """
    try:
        logger.info(f"Processing omics message for patient: {message.get('patient_id')}")

        patient_id = message.get("patient_id")
        drug_list = message.get("drug_list", [])
        gene_expression = message.get("gene_expression", {})

        # TODO: Trigger toxicity predictions for each drug
        # TODO: Check PGx for each gene + drug combination
        # TODO: Check DDI for drug combinations
        # TODO: Store results in database

        logger.info(f"Omics processing completed for patient {patient_id}")

    except Exception as e:
        logger.error(f"Error handling omics message: {e}")


async def stop_kafka_consumer():
    """Stop Kafka consumer."""
    global _kafka_consumer
    if _kafka_consumer:
        await _kafka_consumer.stop()
        logger.info("Kafka consumer stopped")
