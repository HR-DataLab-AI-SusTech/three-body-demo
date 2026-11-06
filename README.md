# Three bodies

A gravity playground: pick or tweak three masses, watch them orbit, save the setup to a shared
gallery, and rate what others saved. It is the HR DataLab's demonstration of its app hosting, a
Streamlit app with a PostgreSQL database, built and deployed by CI to Coolify on the lab's guest pool.

Live at <https://threebody-pilot.apps.twinhub.nl>.

## What it runs

| Service | What it does |
| --- | --- |
| `app` | Streamlit: the simulator and the gallery (`src/threebody/app.py`) |
| `migrate` | Alembic, once, before `app` starts: creates or updates the tables |
| `db` | PostgreSQL 17; the gallery survives restarts and redeploys in its volume |

The physics is Newtonian gravity in a plane, integrated with velocity Verlet (`src/threebody/physics.py`);
the tests check that the figure-eight orbit closes after one period and that energy stays put.

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
