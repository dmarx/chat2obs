# llm_archive/db.py
"""Database connection and session management."""

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger


def get_engine(db_url: str):
    """Create database engine."""
    return create_engine(db_url, echo=False)


def get_session_factory(db_url: str) -> sessionmaker:
    """Create a session factory."""
    engine = get_engine(db_url)
    return sessionmaker(bind=engine)


@contextmanager
def get_session(db_url: str):
    """Context manager for database sessions."""
    factory = get_session_factory(db_url)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_schema(db_url: str, schema_dir: Path | str):
    """Initialize database schema from SQL files."""
    schema_dir = Path(schema_dir)
    engine = get_engine(db_url)
    
    sql_files = sorted(schema_dir.glob("*.sql"))
    
    if not sql_files:
        logger.warning(f"No SQL files found in {schema_dir}")
        return
    
    with engine.connect() as conn:
        for sql_file in sql_files:
            logger.info(f"Executing {sql_file.name}")
            sql = sql_file.read_text()
            
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    logger.debug(f"Statement note: {e}")
            
            conn.commit()
    
    logger.info("Schema initialization complete")


def reset_schema(db_url: str, schema_dir: Path | str | None = None):
    """Drop and recreate schemas (destructive!)."""
    engine = get_engine(db_url)
    
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS derived CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))
        conn.commit()
    
    logger.info("Schemas dropped")
    
    if schema_dir:
        init_schema(db_url, schema_dir)