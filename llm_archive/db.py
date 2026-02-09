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


def _create_pg_schemas(engine) -> None:
    """Create PostgreSQL schema namespaces and extensions."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS derived"))
        conn.commit()


def _create_tables(engine) -> None:
    """Create all ORM-defined tables via Base.metadata.create_all."""
    from llm_archive.models import Base
    import llm_archive.models.annotations  # noqa: F401 — register factory models

    Base.metadata.create_all(engine)


def _seed_sources(engine) -> None:
    """Seed raw.sources if empty."""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM raw.sources")).scalar()
        if count == 0:
            conn.execute(text("""
                INSERT INTO raw.sources (id, display_name, has_native_trees, role_vocabulary)
                VALUES
                    ('chatgpt', 'ChatGPT', true, ARRAY['user', 'assistant', 'system', 'tool']),
                    ('claude', 'Claude', false, ARRAY['user', 'assistant'])
            """))
        conn.commit()


def _create_annotation_union_views(engine) -> None:
    """Generate *_annotations_all union views for each entity type.

    These convenience views union all 4 value-type tables per entity,
    providing a single queryable view of all annotations.
    """
    from llm_archive.annotations.core import EntityType, ValueType

    with engine.connect() as conn:
        for et in EntityType:
            prefix = et.value
            parts = []
            for vt in ValueType:
                table = f"derived.{prefix}_annotations_{vt.value}"
                if vt == ValueType.FLAG:
                    parts.append(
                        f"SELECT id, entity_id, annotation_key, "
                        f"NULL::text AS annotation_value, "
                        f"'{vt.value}' AS value_type, "
                        f"confidence, reason, source, created_at "
                        f"FROM {table}"
                    )
                else:
                    parts.append(
                        f"SELECT id, entity_id, annotation_key, "
                        f"annotation_value::text, "
                        f"'{vt.value}' AS value_type, "
                        f"confidence, reason, source, created_at "
                        f"FROM {table}"
                    )

            view_name = f"derived.{prefix}_annotations_all"
            union_sql = "\nUNION ALL\n".join(parts)
            conn.execute(text(
                f"CREATE OR REPLACE VIEW {view_name} AS\n{union_sql}"
            ))

        conn.commit()


def _execute_view_files(engine, schema_dir: Path) -> None:
    """Execute SQL files that define views (not tables).

    Skips files that only define tables/extensions/seeds (handled by ORM).
    """
    if not schema_dir.exists():
        return

    for sql_file in sorted(schema_dir.glob("*.sql")):
        sql = sql_file.read_text()
        sql_upper = sql.upper()

        # Only execute files containing view definitions
        if "CREATE OR REPLACE VIEW" not in sql_upper and "CREATE VIEW" not in sql_upper:
            continue

        logger.info("Executing views from {}", sql_file.name)
        with engine.connect() as conn:
            for stmt in sql.split(";"):
                stmt = stmt.strip()
                if not stmt:
                    continue
                stmt_upper = stmt.upper()
                if "CREATE" in stmt_upper and "VIEW" in stmt_upper:
                    try:
                        conn.execute(text(stmt))
                    except Exception as e:
                        logger.debug("View statement note: {}", e)
            conn.commit()


def init_schema(db_url: str, schema_dir: Path | str | None = None) -> None:
    """Initialize database schema.

    1. Create PostgreSQL schema namespaces (raw, derived) + extensions
    2. Create all ORM-defined tables
    3. Seed raw.sources lookup table
    4. Create annotation union views (*_annotations_all)
    5. Execute additional view SQL files from schema_dir
    """
    engine = get_engine(db_url)

    _create_pg_schemas(engine)
    _create_tables(engine)
    _seed_sources(engine)
    _create_annotation_union_views(engine)

    if schema_dir:
        _execute_view_files(engine, Path(schema_dir))

    logger.info("Schema initialization complete")


def reset_schema(db_url: str, schema_dir: Path | str | None = None) -> None:
    """Drop and recreate schemas (destructive!)."""
    engine = get_engine(db_url)

    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS derived CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))
        conn.commit()

    logger.info("Schemas dropped")
    init_schema(db_url, schema_dir)
