"""The gallery against a real PostgreSQL. Needs DATABASE_URL; CI gives it a service container.

The schema comes from the Alembic migrations, exactly as in production, so these also prove that
the migrations and the models agree.
"""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

from threebody import store
from threebody.presets import FIGURE_EIGHT, PYTHAGOREAN

pytestmark = pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="needs DATABASE_URL")

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def engine() -> Engine:
    cfg = Config(str(ROOT / "alembic.ini"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    return create_engine(os.environ["DATABASE_URL"])


@pytest.fixture(autouse=True)
def empty(engine: Engine):
    with engine.begin() as c:
        c.execute(text("TRUNCATE ratings, setups RESTART IDENTITY CASCADE"))


def test_a_saved_setup_is_there_on_the_next_visit(engine):
    sid = store.save_setup(engine, "  My eight  ", "a classic", FIGURE_EIGHT)
    [item] = store.gallery(engine)
    assert (item.id, item.name, item.description) == (sid, "My eight", "a classic")
    assert item.config == FIGURE_EIGHT
    assert (item.rating, item.votes) == (None, 0)


def test_ratings_average_and_one_per_visitor(engine):
    sid = store.save_setup(engine, "eight", None, FIGURE_EIGHT)
    assert store.rate(engine, sid, "visitor-a", 5)
    assert store.rate(engine, sid, "visitor-b", 2)
    assert not store.rate(engine, sid, "visitor-a", 1)  # a second vote from the same visitor
    [item] = store.gallery(engine)
    assert (item.rating, item.votes) == (3.5, 2)


def test_best_first_then_newest_first(engine):
    low = store.save_setup(engine, "low", None, FIGURE_EIGHT)
    high = store.save_setup(engine, "high", None, PYTHAGOREAN)
    store.rate(engine, low, "v", 1)
    store.rate(engine, high, "v", 5)
    assert [i.name for i in store.gallery(engine, "best")] == ["high", "low"]
    assert [i.name for i in store.gallery(engine, "newest")] == ["high", "low"]


def test_deleting_a_setup_takes_its_ratings(engine):
    sid = store.save_setup(engine, "gone", None, FIGURE_EIGHT)
    store.rate(engine, sid, "v", 4)
    assert store.delete_setup(engine, sid)
    assert store.gallery(engine) == []
    with engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM ratings")) == 0


def test_bad_input_is_refused(engine):
    with pytest.raises(ValueError):
        store.save_setup(engine, "   ", None, FIGURE_EIGHT)
    sid = store.save_setup(engine, "x" * 500, "y" * 5000, FIGURE_EIGHT)
    [item] = store.gallery(engine)
    assert item.id == sid and len(item.name) == store.NAME_MAX
    assert item.description is not None and len(item.description) == store.DESCRIPTION_MAX
    with pytest.raises(ValueError):
        store.rate(engine, sid, "v", 6)


def test_a_full_gallery_refuses_new_setups(engine, monkeypatch):
    monkeypatch.setattr(store, "MAX_SETUPS", 2)
    store.save_setup(engine, "one", None, FIGURE_EIGHT)
    store.save_setup(engine, "two", None, FIGURE_EIGHT)
    with pytest.raises(store.GalleryFullError):
        store.save_setup(engine, "three", None, FIGURE_EIGHT)


def _presets():
    from threebody.presets import PRESETS

    return {name: (p.description, p.config) for name, p in PRESETS.items()}


def test_seeding_adds_the_presets_once_and_keeps_their_ratings(engine):
    presets = _presets()
    assert store.ensure_featured(engine, presets) == (len(presets), 0)
    eight = next(i for i in store.gallery(engine, which="featured") if i.name == "Figure-eight")
    store.rate(engine, eight.id, "v", 5)

    assert store.ensure_featured(engine, presets) == (0, 0)  # a redeploy changes nothing
    changed = {**presets, "Figure-eight": ("a new description", presets["Figure-eight"][1])}
    assert store.ensure_featured(engine, changed) == (0, 1)  # updated in place

    again = next(i for i in store.gallery(engine, which="featured") if i.name == "Figure-eight")
    assert (again.id, again.description, again.rating) == (eight.id, "a new description", 5.0)


def test_the_gallery_separates_featured_and_visitors_setups(engine):
    store.ensure_featured(engine, _presets())
    store.save_setup(engine, "Figure-eight", "a visitor may reuse the name", FIGURE_EIGHT)
    featured = store.gallery(engine, which="featured")
    visitors = store.gallery(engine, which="visitors")
    assert all(i.featured for i in featured) and len(featured) == len(_presets())
    assert [i.name for i in visitors] == ["Figure-eight"] and not visitors[0].featured
    assert len(store.gallery(engine, which="all")) == len(featured) + 1
