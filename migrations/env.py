"""Alembic's runner: migrations go against DATABASE_URL, online, in one transaction each."""

import os

from alembic import context
from sqlalchemy import create_engine

from threebody.store import Base

target_metadata = Base.metadata

engine = create_engine(os.environ["DATABASE_URL"])
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
