"""Put the presets into the gallery as featured setups: `python -m threebody.seed`.

Run after the migrations on every deploy. A featured setup is matched by name and updated in place,
so the presets in code stay the source while the ratings visitors gave them are kept.
"""

from __future__ import annotations

from threebody import store
from threebody.presets import PRESETS


def main() -> None:
    added, updated = store.ensure_featured(
        store.engine_from_env(),
        {name: (p.description, p.config) for name, p in PRESETS.items()},
    )
    print(f"featured setups: {added} added, {updated} updated, {len(PRESETS)} in all")


if __name__ == "__main__":
    main()
