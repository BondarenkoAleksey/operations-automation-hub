from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from operations_automation_hub.core.settings import Settings

settings = Settings()

engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)
