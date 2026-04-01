"""Kafka event publisher for omics processing."""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from aiokafka import AIOKafkaProducer
import asyncio

logger = logging.getLogger(__name__)


class OmicsKafkaPublisher:
    """Publish omics processing events to Kafka."""

    TOPIC_OMICS_PROCESSED = "omics_processed"
    TOPIC_OMICS_ERROR = "omics_error"
    TOPIC_TOXICITY_INTEGRATION = "toxicity_integration"

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize Kafka publisher.

        Args:
            bootstrap_servers: Kafka bootstrap servers
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            self.logger.info(f"Kafka producer started: {self.bootstrap_servers}")
        except Exception as e:
            self.logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self) -> None:
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self.logger.info("Kafka producer stopped")

    async def publish_rna_processed(
        self,
        patient_id: UUID,
        record_count: int,
        processing_duration: float,
        significant_genes: int,
        upregulated: int,
        downregulated: int
    ) -> str:
        """
        Publish RNA-seq processing completion event.

        Args:
            patient_id: Patient UUID
            record_count: Number of genes processed
            processing_duration: Processing time in seconds
            significant_genes: Significant gene count (padj < 0.05)
            upregulated: Upregulated gene count
            downregulated: Downregulated gene count

        Returns:
            Message ID
        """
        event = {
            "event_type": "omics_processed",
            "patient_id": str(patient_id),
            "data_type": "rna-seq",
            "result_table": "rna_results",
            "record_count": record_count,
            "significant_genes": significant_genes,
            "upregulated_genes": upregulated,
            "downregulated_genes": downregulated,
            "processing_duration_seconds": processing_duration,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }

        return await self._publish(self.TOPIC_OMICS_PROCESSED, event, str(patient_id))

    async def publish_proteomics_processed(
        self,
        patient_id: UUID,
        record_count: int,
        processing_duration: float,
        detected_proteins: int,
        drug_targets: int,
        enzymes: int
    ) -> str:
        """
        Publish proteomics processing completion event.

        Args:
            patient_id: Patient UUID
            record_count: Number of proteins processed
            processing_duration: Processing time in seconds
            detected_proteins: Proteins with LFQ > 0
            drug_targets: Drug target proteins
            enzymes: Enzyme proteins

        Returns:
            Message ID
        """
        event = {
            "event_type": "omics_processed",
            "patient_id": str(patient_id),
            "data_type": "proteomics",
            "result_table": "protein_results",
            "record_count": record_count,
            "detected_proteins": detected_proteins,
            "drug_target_proteins": drug_targets,
            "enzyme_proteins": enzymes,
            "processing_duration_seconds": processing_duration,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }

        return await self._publish(self.TOPIC_OMICS_PROCESSED, event, str(patient_id))

    async def publish_omics_error(
        self,
        patient_id: UUID,
        data_type: str,
        error_message: str,
        file_path: Optional[str] = None
    ) -> str:
        """
        Publish omics processing error event.

        Args:
            patient_id: Patient UUID
            data_type: rna-seq or proteomics
            error_message: Error description
            file_path: Optional file path that caused error

        Returns:
            Message ID
        """
        event = {
            "event_type": "omics_error",
            "patient_id": str(patient_id),
            "data_type": data_type,
            "error_message": error_message,
            "file_path": file_path,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error"
        }

        return await self._publish(self.TOPIC_OMICS_ERROR, event, str(patient_id))

    async def publish_toxicity_integration(
        self,
        patient_id: UUID,
        rna_genes: list,
        protein_targets: list,
        enriched_features: Dict[str, Any]
    ) -> str:
        """
        Publish omics features to Toxicity Guard integration.

        This notifies Dev 3's Toxicity module to incorporate RNA and protein signals.

        Args:
            patient_id: Patient UUID
            rna_genes: List of significant genes (gene_id)
            protein_targets: List of drug target proteins
            enriched_features: Dictionary of RNA/protein features

        Returns:
            Message ID
        """
        event = {
            "event_type": "omics_integration",
            "patient_id": str(patient_id),
            "data_source": "omics_pipeline",
            "rna_genes": rna_genes,
            "rna_gene_count": len(rna_genes),
            "protein_targets": protein_targets,
            "protein_count": len(protein_targets),
            "enriched_features": enriched_features,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return await self._publish(self.TOPIC_TOXICITY_INTEGRATION, event, str(patient_id))

    async def _publish(self, topic: str, event: Dict[str, Any], partition_key: str) -> str:
        """
        Internal method to publish event to Kafka.

        Args:
            topic: Kafka topic name
            event: Event payload
            partition_key: Key for partitioning (usually patient_id)

        Returns:
            Message ID (metadata.offset)
        """
        if not self.producer:
            self.logger.warning("Kafka producer not started, skipping publication")
            return "offline"

        try:
            metadata = await self.producer.send_and_wait(
                topic,
                value=event,
                key=partition_key.encode('utf-8')
            )
            msg_id = f"{metadata.partition}:{metadata.offset}"
            self.logger.info(f"Published to {topic}: {msg_id}")
            return msg_id
        except Exception as e:
            self.logger.error(f"Failed to publish to {topic}: {e}")
            raise


class OmicsEventConsumer:
    """Consume omics events (for testing/integration)."""

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """Initialize consumer."""
        self.bootstrap_servers = bootstrap_servers
        self.logger = logging.getLogger(__name__)

    async def consume_omics_events(self, topic: str, group_id: str, max_events: int = 10):
        """
        Consume omics events from Kafka.

        Args:
            topic: Kafka topic to consume from
            group_id: Consumer group ID
            max_events: Maximum events to consume
        """
        from aiokafka import AIOKafkaConsumer

        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest'
        )

        try:
            await consumer.start()
            self.logger.info(f"Started consuming from {topic}")

            count = 0
            async for message in consumer:
                self.logger.info(f"Event {count}: {message.value}")
                count += 1
                if count >= max_events:
                    break
        finally:
            await consumer.stop()


async def publish_test_event():
    """Test publishing an omics event."""
    from uuid import uuid4

    publisher = OmicsKafkaPublisher()
    await publisher.start()

    try:
        patient_id = uuid4()

        # Test RNA-seq event
        rna_id = await publisher.publish_rna_processed(
            patient_id=patient_id,
            record_count=18_000,
            processing_duration=45.2,
            significant_genes=1_234,
            upregulated=456,
            downregulated=789
        )
        logger.info(f"Published RNA event: {rna_id}")

        # Test proteomics event
        proteomics_id = await publisher.publish_proteomics_processed(
            patient_id=patient_id,
            record_count=5_000,
            processing_duration=30.5,
            detected_proteins=3_500,
            drug_targets=450,
            enzymes=1_200
        )
        logger.info(f"Published proteomics event: {proteomics_id}")

        # Test toxicity integration
        toxicity_id = await publisher.publish_toxicity_integration(
            patient_id=patient_id,
            rna_genes=["BRCA1", "TP53", "EGFR"],
            protein_targets=["CYP3A4", "CYP2C9"],
            enriched_features={"expression_pattern": "high", "validation_score": 0.95}
        )
        logger.info(f"Published toxicity integration: {toxicity_id}")

    finally:
        await publisher.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(publish_test_event())
