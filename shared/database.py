from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class used by SQLAlchemy persistence records."""


class Database:
    """Create database sessions with automatic commit and rollback behavior."""

    def __init__(self, url: str = "sqlite:///edms.db") -> None:
        self.engine: Engine = create_engine(url)
        self._session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    def create_schema(self) -> None:
        """Import repository mappings and create tables for the current application."""
        import authentication.repositories.user_repository
        import catalog.repositories.records
        import inventory.repositories.inventory_repository
        import logistics.repositories.records
        import procurement.repositories.purchase_order_repository
        import sales.repositories.records

        Base.metadata.create_all(self.engine)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Commit on success; roll back and re-raise if work fails."""
        with self._session_factory.begin() as session:
            yield session