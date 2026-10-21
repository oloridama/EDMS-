from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from authentication.models.user import Role, User
from shared.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserRecord(Base):
    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tokens: Mapped[list[AuthTokenRecord]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class AuthTokenRecord(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("auth_users.id"), index=True)
    token_digest: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    user: Mapped[UserRecord] = relationship(back_populates="tokens")


def user_from_record(record: UserRecord) -> User:
    return User(
        user_id=record.id,
        username=record.username,
        email=record.email,
        password_hash=record.password_hash,
        role=Role(record.role),
        is_active=record.is_active,
    )


class UserRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: Role,
        is_active: bool = True,
    ) -> User:
        record = UserRecord(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role.value,
            is_active=is_active,
        )
        self.db_session.add(record)
        self.db_session.flush()
        return user_from_record(record)

    def get_by_username(self, username: str) -> User | None:
        record = self.db_session.scalar(
            select(UserRecord).where(UserRecord.username == username)
        )
        return user_from_record(record) if record else None

    def get_by_email(self, email: str) -> User | None:
        record = self.db_session.scalar(
            select(UserRecord).where(UserRecord.email == email)
        )
        return user_from_record(record) if record else None

    def get_by_id(self, user_id: int) -> User | None:
        record = self.db_session.get(UserRecord, user_id)
        return user_from_record(record) if record else None

    def count(self) -> int:
        return len(self.db_session.scalars(select(UserRecord.id)).all())

    def set_active(self, user_id: int, is_active: bool) -> User | None:
        record = self.db_session.get(UserRecord, user_id)
        if record is None:
            return None
        record.is_active = is_active
        self.db_session.flush()
        return user_from_record(record)


class AuthTokenRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, user_id: int, token_digest: str, ttl: timedelta) -> datetime:
        expires_at = utc_now() + ttl
        self.db_session.add(
            AuthTokenRecord(
                user_id=user_id,
                token_digest=token_digest,
                expires_at=expires_at,
            )
        )
        self.db_session.flush()
        return expires_at

    def resolve(self, token_digest: str) -> User | None:
        record = self.db_session.scalar(
            select(AuthTokenRecord).where(
                AuthTokenRecord.token_digest == token_digest
            )
        )
        if record is None or record.revoked_at is not None:
            return None
        if record.expires_at <= utc_now():
            return None
        return user_from_record(record.user)

    def revoke(self, token_digest: str) -> None:
        record = self.db_session.scalar(
            select(AuthTokenRecord).where(
                AuthTokenRecord.token_digest == token_digest
            )
        )
        if record is not None and record.revoked_at is None:
            record.revoked_at = utc_now()
            self.db_session.flush()
