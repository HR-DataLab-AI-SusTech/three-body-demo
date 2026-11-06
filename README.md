# Three bodies

A gravity playground: pick one of 16 famous orbits or tweak your own three masses, watch them,
save the setup to a shared gallery, and rate what others saved. It is the HR DataLab's demonstration of its app hosting, a
Streamlit app with a PostgreSQL database, built and deployed by CI to Coolify on the lab's guest pool.

Live at <https://threebody-pilot.apps.twinhub.nl>.

## What it runs

| Service | What it does |
| --- | --- |
| `app` | Streamlit: the simulator and the gallery (`src/threebody/app.py`) |
| `migrate` | once, before `app` starts: Alembic brings the tables up to date, then the famous orbits are seeded into the gallery as featured setups (`python -m threebody.seed`) |
| `db` | PostgreSQL 17; the gallery survives restarts and redeploys in its volume |

The physics is Newtonian gravity in a plane, integrated by DOP853, an adaptive eighth-order
Runge-Kutta method (`src/threebody/physics.py`). The famous orbits (`src/threebody/presets.py`) are
the figure-eight, Lagrange's triangle, Burrau's Pythagorean problem and thirteen orbits from
Šuvakov & Dmitrašinović, *Phys. Rev. Lett.* 110, 114301 (2013); the tests check that every periodic
one returns to its start after its published period, and that energy stays put.

## Develop

```bash
uv sync
uv run pytest                      # physics; the database tests need DATABASE_URL (below)
SERVICE_PASSWORD_POSTGRES=dev SERVICE_PASSWORD_ADMIN=dev \
  docker compose -f compose.yaml -f compose.dev.yaml up --build
```

The dev compose builds the image locally and publishes the app on <http://localhost:8501>.

## How it reaches the internet

A push to `main` runs `.github/workflows/ci.yml`: lint, types and tests against a real PostgreSQL,
then the image is built, scanned and pushed to GHCR with a provenance attestation, and the deploy job
hands Coolify the compose file with the image pinned to that digest and asks it to deploy. A pull
request runs the checks and never deploys. Coolify's own deploy-on-push is off, so nothing that
failed CI goes live.

Secrets are not in this repository: Coolify generates the database password and the admin code.
