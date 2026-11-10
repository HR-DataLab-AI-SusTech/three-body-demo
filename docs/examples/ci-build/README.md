# Build in GitHub Actions, run the image on Coolify

For an app whose build needs more memory than your Coolify server has (a build's peak is often
several times what the app uses while running). A GitHub runner builds and scans the image, pushes it
to GHCR, and Coolify runs that exact image by digest, so your server never builds.

**Status.** Generalised from the `ci.yml` and `deploy-to-coolify.sh` this repository ran before
commit `81327d6` ("Coolify builds from GitHub"). The generalised files have not been run; expect to
fix a detail. On the HR DataLab's panel the deploy step does not get through as written: the panel's
API sits behind the lab's email check, which a workflow cannot pass. Ask your sponsor before you
build on this recipe. If the build only needs a lighter Dockerfile (`uv`, multi-stage, slim image: see this
repository's `Dockerfile`), do that instead: it is less to maintain.

## What changes in your repository

1. **`compose.yaml`**: replace `build: .` with an image line that has a default,
   `image: ${IMAGE:-ghcr.io/<owner>/<repo>:main}` (lower case), on every service built from your code.
2. **`.github/workflows/ci.yml`**: copy [`ci.yml`](ci.yml) and replace the `checks` job with your tests.
3. **`.github/scripts/deploy-to-coolify.sh`**: copy [`deploy-to-coolify.sh`](deploy-to-coolify.sh).
4. **In Coolify**: create the application once as a **Docker Compose** service from this
   `compose.yaml`, and **turn off its deploy on push** so nothing reaches the site without passing CI.
   The server must be able to pull the image: make the GHCR package public, or add a registry
   login for `ghcr.io` to the server.
5. **In GitHub → Settings → Secrets and variables → Actions**:
   - secret `COOLIFY_TOKEN`: a Coolify API token from inside your team, with Write and Deploy only;
   - variables `COOLIFY_URL` (`https://panel.twinhub.nl`), `COOLIFY_SERVICE_UUID` (from the
     service's URL in the panel), `APP_URL` (your app's address), `APP_PORT` (the port it listens
     on) and `IMAGE_DEFAULT` (the exact `${IMAGE:-ghcr.io/<owner>/<repo>:main}` text from step 1).
6. Create a GitHub environment named `production` (the deploy job uses it).

Until the secret and variables exist the deploy step prints a notice and skips, so the image build
can be tried first.
