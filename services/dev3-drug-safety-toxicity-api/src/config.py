import logging
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # App Configuration
    APP_ENV: str = "development"
    APP_PORT: int = 8003
    LOG_LEVEL: str = "INFO"

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/theragenome"

    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_OMICS_PROCESSED: str = "omics_processed"

    # External API Keys
    PHARMGKB_API_KEY: str = ""
    DRUGBANK_API_KEY: str = ""

    # Service URLs
    DEV1_SERVICE_URL: str = "http://localhost:8001"

    # ML Model
    TOXICITY_MODEL_PATH: str = "models/toxicity_model.joblib"

    class Config:
        env_file = ".env"


settings = Settings()


def configure_logging():
    """Configure application logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s %(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Suppress verbose library logs
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("aiokafka").setLevel(logging.WARNING)


# Configure logging on module load
configure_logging()
