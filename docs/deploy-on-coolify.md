# Deploy this app on Coolify

You will fork this repository, point your [Coolify](https://coolify.io) team at the fork, and get
the app on a public HTTPS address that redeploys on every push to `main`. About fifteen minutes.

> Written for the HR DataLab's panel (<https://panel.apps.twinhub.nl>). Button names follow
> Coolify 4.x and can differ a little between versions.

## What you need

- A Coolify team with a server (a *tenant*). Your sponsor at the lab arranges it.
- A GitHub account.
- The address you were given, for example `https://threebody-myteam.apps.twinhub.nl`.

## What gets deployed

[`compose.yaml`](../compose.yaml) describes three services and Coolify runs them together:

| Service | Job |
| --- | --- |
| `app` | Streamlit on port 8501, the only service with a public address |
| `migrate` | runs once before `app`: creates the tables, then seeds the famous orbits, then exits |
| `db` | PostgreSQL 17 with a volume, so the gallery survives restarts and redeploys |

`app` and `migrate` are built from the [`Dockerfile`](../Dockerfile) in this repository; Coolify does
the build on your server. The two passwords are `${SERVICE_PASSWORD_POSTGRES}` and
`${SERVICE_PASSWORD_ADMIN}`: Coolify sees the `SERVICE_PASSWORD_` prefix, generates a value once and
fills it in. Nothing secret is in the repository, and you never type a password.

## Steps

1. **Fork** this repository on GitHub (**Fork**, top right). A fork is yours to push to; Coolify
   needs a repository you control.
2. In the panel, open **Projects → New** (or an existing project) → **Add resource**.
3. Choose the repository type:
   - **Public repository**: paste the fork's URL. Simplest, but pushes only deploy automatically
     after you add a webhook (step 8).
   - **Private repository with GitHub App** (or with a deploy key): the better choice for anything
     you do not want to publish. Pushes deploy automatically. Ask your sponsor if the panel has no
     GitHub App yet.
4. Pick the server, branch `main`, and **Build pack: Docker Compose**. Leave the compose location
   at `/compose.yaml`.
5. Continue to the resource. Under **Domains**, find the line for the service `app` and enter your
   address **with the port**: `https://threebody-myteam.apps.twinhub.nl:8501`. Without `:8501`
   the proxy tries port 80 and shows a bad gateway.
6. There are no environment variables to set. Check the resource's **Environment Variables** tab: it
   lists `SERVICE_PASSWORD_POSTGRES` and `SERVICE_PASSWORD_ADMIN`, already generated. The admin
   password is the code that lets you delete setups in the gallery; read it there when you need it.
7. Press **Deploy**. Open the deployment log. You should see the image build, then `db` become
   healthy, then `migrate` run `alembic upgrade head` and exit with code 0, then `app` start. The
   first build takes a few minutes; later ones reuse the cache.
8. **Automatic deploys.** With the GitHub App this is already on. With a public repository, copy the
   webhook URL and secret from the resource's **Webhooks** section into your fork's
   **Settings → Webhooks** (content type `application/json`, push events), and make sure the
   resource's **Auto Deploy** switch is on.
9. Visit your address. The first request can take a moment while the certificate is issued. The
   gallery already holds the sixteen famous orbits.

## Day to day

- **Change the app**: edit, push to `main`, Coolify rebuilds and redeploys.
- **Your data stays**: the gallery lives in the `db-data` volume. A redeploy replaces the containers,
  not the volume.
- **A schema change** is a new file in `migrations/versions/`. `migrate` applies it before the new
  `app` starts, on every deploy.
- **Roll back**: the resource's **Deployments** list shows earlier deployments; redeploy one.
- **Logs and shell**: per service, in the resource. `migrate` is a one-shot job, so its log is the
  place to look when a deploy stops before the app starts.

## Keep bad code from going live

Coolify deploys whatever lands on the branch; it does not wait for GitHub Actions. This repository's
[CI](../.github/workflows/ci.yml) runs format, lint, types and tests (against a real PostgreSQL) on
every push and pull request, so the habit that keeps the site safe is:

1. Work on a branch and open a pull request.
2. Merge only when CI is green.

If you want the server to be stricter, GitHub's **Settings → Branches** can require the check before
merging (private repositories need a paid plan for this).

## Use it for your own app

What this repository shows, and your app needs too:

- A `Dockerfile` that listens on one port and runs without root. Keep dependencies locked
  (`uv.lock`) so a rebuild gives the same app.
- A `compose.yaml` with `build: .` for your code, other services as ordinary images, and
  `${SERVICE_PASSWORD_*}` for any password.
- A one-shot service for migrations, with `depends_on: condition: service_completed_successfully`
  on the app. Mark it `coolify.proxy=false` so Coolify does not try to route to it.
- A healthcheck on the database and `condition: service_healthy` where something waits for it.

If your app is a single container with no database, skip Compose: choose **Dockerfile** as the build
pack, or let Coolify detect the language, and set the port in the resource.

## When something goes wrong

| You see | Check |
| --- | --- |
| Bad gateway | the domain has the port (`:8501`); `app` is running, not restarting |
| Deploy stops at `migrate` | its log; a failing migration keeps `app` from starting, by design |
| Build killed or very slow | your server ran out of memory during the build; ask your sponsor for more, or build the image in GitHub Actions and deploy it (below) |
| No certificate | the address resolves to the pool (`dig +short <address>`); wait a minute and reload |
| A push did not deploy | the webhook's recent deliveries in GitHub; the resource's Auto Deploy switch |

## Later: build in CI, deploy a pinned image

Building on your server is the simple route. The stricter one builds the image in GitHub Actions,
scans it, pushes it to a registry, and tells Coolify to run that exact image by digest, so nothing
that failed CI reaches the site and the server never builds. It is more setup (a registry package
the server can pull, a Coolify API token, two repository variables). An earlier version of this
repository did exactly that; see the git history before the commit "Coolify builds from GitHub".
