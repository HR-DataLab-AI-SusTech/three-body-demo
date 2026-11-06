#!/usr/bin/env bash
# Point the Coolify service at the image CI just built and scanned, then deploy it.
#
# The compose file in this repository is the source: its image line is replaced by IMAGE_REF (a
# digest, so exactly the scanned bytes run) and the whole file, with the app's URL, is PATCHed into
# the service. Prints status codes only; a response that carried the token is never echoed.
set -euo pipefail

if [ -z "${COOLIFY_TOKEN:-}" ] || [ -z "${COOLIFY_URL:-}" ] || [ -z "${COOLIFY_SERVICE_UUID:-}" ]; then
  echo "::notice::Deploy skipped: COOLIFY_TOKEN, COOLIFY_URL or COOLIFY_SERVICE_UUID is not set yet."
  exit 0
fi
case "$IMAGE_REF" in *@sha256:*) ;; *) echo "::error::IMAGE_REF is not a digest: $IMAGE_REF"; exit 1;; esac

compose=$(sed "s#\${IMAGE:-ghcr.io/hr-datalab-ai-sustech/three-body-demo:main}#${IMAGE_REF}#g" compose.yaml)
grep -q "$IMAGE_REF" <<<"$compose" || { echo "::error::the image line was not replaced"; exit 1; }

cfg=$(mktemp); chmod 600 "$cfg"; trap 'rm -f "$cfg" /tmp/coolify.$$' EXIT
printf 'header = "Authorization: Bearer %s"\nheader = "Content-Type: application/json"\n' \
  "$COOLIFY_TOKEN" > "$cfg"

body=$(python3 -c 'import base64, json, sys
print(json.dumps({"docker_compose_raw": base64.b64encode(sys.argv[1].encode()).decode(),
                  "urls": [{"name": "app", "url": sys.argv[2] + ":8501"}]}))' "$compose" "$APP_URL")

code=$(curl -sS -o /tmp/coolify.$$ -w '%{http_code}' -K "$cfg" -X PATCH --data "$body" \
  "$COOLIFY_URL/api/v1/services/$COOLIFY_SERVICE_UUID")
echo "update the service -> $code"
case "$code" in 2*) ;; *) exit 1;; esac

code=$(curl -sS -o /tmp/coolify.$$ -w '%{http_code}' -K "$cfg" -X POST \
  "$COOLIFY_URL/api/v1/deploy?uuid=$COOLIFY_SERVICE_UUID")
echo "deploy -> $code"
case "$code" in 2*) ;; *) exit 1;; esac
echo "::notice::Deploying $IMAGE_REF to $APP_URL"
