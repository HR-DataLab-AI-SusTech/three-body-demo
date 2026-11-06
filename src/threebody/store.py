"""The gallery in PostgreSQL: saved setups and the ratings visitors give them.

The schema itself is Alembic's (migrations/); these models describe it for queries.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Engine,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
    create_engine,
    delete,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from threebody.config import SetupConfig

# A public form writes here, so the gallery has a ceiling; a full gallery refuses new setups.
MAX_SETUPS = 2000
NAME_MAX = 60
DESCRIPTION_MAX = 280


class Base(DeclarativeBase):
    pass


class Setup(Base):
    __tablename__ = "setups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX))
    description: Mapped[str | None] = mapped_column(String(DESCRIPTION_MAX))
    config: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("setup_id", "visitor", name="one_rating_per_visitor"),
        CheckConstraint("stars BETWEEN 1 AND 5", name="stars_one_to_five"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    setup_id: Mapped[int] = mapped_column(ForeignKey("setups.id", ondelete="CASCADE"), index=True)
    stars: Mapped[int] = mapped_column(SmallInteger)
    visitor: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GalleryFullError(Exception):
    pass


@dataclass(frozen=True)
class GalleryItem:
    id: int
    name: str
    description: str | None
    config: SetupConfig
    created_at: datetime
    rating: float | None
    votes: int


def engine_from_env() -> Engine:
    return create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)


def save_setup(engine: Engine, name: str, description: str | None, config: SetupConfig) -> int:
    name = name.strip()[:NAME_MAX]
    if not name:
        raise ValueError("a setup needs a name")
    description = (description or "").strip()[:DESCRIPTION_MAX] or None
    with Session(engine) as s, s.begin():
        if (s.scalar(select(func.count()).select_from(Setup)) or 0) >= MAX_SETUPS:
            raise GalleryFullError
        row = Setup(name=name, description=description, config=config.model_dump(mode="json"))
        s.add(row)
        s.flush()
        return row.id


def gallery(
    engine: Engine, order: Literal["best", "newest"] = "best", limit: int = 100
) -> list[GalleryItem]:
    avg = func.avg(Rating.stars).label("rating")
    votes = func.count(Rating.id).label("votes")
    q = select(Setup, avg, votes).outerjoin(Rating).group_by(Setup.id)
    if order == "best":
        q = q.order_by(avg.desc().nulls_last(), votes.desc(), Setup.created_at.desc())
    else:
        q = q.order_by(Setup.created_at.desc())
    with Session(engine) as s:
        return [
            GalleryItem(
                id=setup.id,
                name=setup.name,
                description=setup.description,
                config=SetupConfig.model_validate(setup.config),
                created_at=setup.created_at,
                rating=float(rating) if rating is not None else None,
                votes=int(n),
            )
            for setup, rating, n in s.execute(q.limit(limit)).all()
        ]


def rate(engine: Engine, setup_id: int, visitor: str, stars: int) -> bool:
    """Record a rating; False when this visitor already rated this setup."""
    if not 1 <= stars <= 5:
        raise ValueError("stars must be 1 to 5")
    stmt = (
        insert(Rating)
        .values(setup_id=setup_id, visitor=visitor[:64], stars=stars)
        .on_conflict_do_nothing(constraint="one_rating_per_visitor")
        # A row comes back only when the insert happened; an ORM result's rowcount does not say.
        .returning(Rating.id)
    )
    with engine.begin() as c:
        return c.execute(stmt).scalar() is not None


def delete_setup(engine: Engine, setup_id: int) -> bool:
    with Session(engine) as s, s.begin():
        return s.execute(delete(Setup).where(Setup.id == setup_id)).rowcount == 1  # type: ignore[attr-defined]
