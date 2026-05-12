import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator, Optional
import logging

from src.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.host = DB_HOST
        self.port = DB_PORT
        self.database = DB_NAME
        self.user = DB_USER
        self.password = DB_PASSWORD

    def get_connection(self):
        """Establish a database connection"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise

    @contextmanager
    def get_cursor(self, commit: bool = True) -> Generator:
        """Context manager for database operations"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def init_db(self):
        """Initialize database schema"""
        with open('src/schemas/variant_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        with self.get_cursor() as cursor:
            cursor.execute(schema_sql)
        logger.info("Database schema initialized")


# Global database instance
db = DatabaseConnection()
