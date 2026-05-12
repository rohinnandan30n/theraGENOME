import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "genomic_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC_RAW_VARIANTS = os.getenv("KAFKA_TOPIC_RAW_VARIANTS", "raw_variants")

# Storage Configuration
STORAGE_PATH = os.getenv("STORAGE_PATH", "./uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5 * 1024 * 1024))  # 5MB default

# Application Configuration
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_CACHE_TTL_HOURS = int(os.getenv("REDIS_CACHE_TTL_HOURS", "24"))

# External APIs Configuration
GNOMAD_TIMEOUT = int(os.getenv("GNOMAD_TIMEOUT", "10"))
CLINVAR_DOWNLOAD_PATH = os.getenv("CLINVAR_DOWNLOAD_PATH", "./data/clinvar")
