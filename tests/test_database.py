import pytest
from sqlalchemy import text


@pytest.mark.integration
def test_postgres_connection_executes_select_one():
    from operations_automation_hub.database import engine

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        assert result.scalar_one() == 1
