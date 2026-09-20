import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from operations_automation_hub.database import SessionLocal, get_db


@pytest.mark.integration
def test_postgres_connection_executes_select_one():
    from operations_automation_hub.database import engine

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        assert result.scalar_one() == 1


@pytest.mark.integration
def test_session_local_creates_working_session():
    with SessionLocal() as session:
        assert isinstance(session, Session)
        result = session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


@pytest.mark.integration
def test_get_db_yields_working_session():
    gen = get_db()
    try:
        session = next(gen)
        assert isinstance(session, Session)
        result = session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
    finally:
        gen.close()
