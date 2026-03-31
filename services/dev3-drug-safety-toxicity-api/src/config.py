from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_PORT: int = 8003
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/theragenome"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_OMICS_PROCESSED: str = "omics_processed"
    PHARMGKB_API_KEY: str = ""
    DRUGBANK_API_KEY: str = ""
    DEV1_SERVICE_URL: str = "http://localhost:8001"
    TOXICITY_MODEL_PATH: str = "models/toxicity_model.joblib"
    class Config:
        env_file = ".env"

settings = Settings()
