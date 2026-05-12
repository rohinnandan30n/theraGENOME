from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import logging
from typing import Dict, Any

from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_RAW_VARIANTS

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    def __init__(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}")
            raise

    def publish_ingestion_event(self, job_id: str, event_data: Dict[str, Any]) -> bool:
        """Publish raw variant ingestion event to Kafka"""
        event_payload = {
            'job_id': job_id,
            'event_type': 'raw_variants_ingested',
            'timestamp': event_data.get('timestamp'),
            'variant_count': event_data.get('variant_count'),
            'filename': event_data.get('filename'),
            'status': event_data.get('status'),
            'errors': event_data.get('errors', [])
        }
        
        try:
            future = self.producer.send(
                KAFKA_TOPIC_RAW_VARIANTS,
                value=event_payload
            )
            # Wait for the record to be sent with a timeout
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Published event to {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to publish event: {str(e)}")
            return False

    def close(self):
        """Close producer connection"""
        try:
            self.producer.close()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {str(e)}")


# Global producer instance
producer = None


def get_producer() -> KafkaEventProducer:
    """Get or create global Kafka producer"""
    global producer
    if producer is None:
        producer = KafkaEventProducer()
    return producer
