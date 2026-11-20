
#!/usr/bin/env bash
set -euo pipefail

STAGING_CONTAINER="devsecops-flask-staging"
ZAP_NETWORK="devsecops-zap-staging-${BUILD_NUMBER:-local}"
REPORT_DIR="$(pwd)/zap-reports"

mkdir -p "$REPORT_DIR"

cleanup() {
    echo "Cleaning up temporary ZAP network..."

    docker network disconnect \
        "$ZAP_NETWORK" "$STAGING_CONTAINER" \
        >/dev/null 2>&1 || true

    docker network rm "$ZAP_NETWORK" \
        >/dev/null 2>&1 || true
}

trap cleanup EXIT

echo "Creating ZAP scan network..."
docker network create "$ZAP_NETWORK"

echo "Connecting deployed staging application..."
docker network connect "$ZAP_NETWORK" "$STAGING_CONTAINER"

APP_URL="http://${STAGING_CONTAINER}:5000"

echo "Checking deployed application..."
docker exec "$STAGING_CONTAINER" \
    python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)"

echo "Running OWASP ZAP against deployed staging..."

docker run --rm \
    --network "$ZAP_NETWORK" \
    --user "$(id -u):$(id -g)" \
    --workdir /zap/wrk \
    --entrypoint /bin/bash \
    -e HOME=/zap/wrk \
    -e JAVA_TOOL_OPTIONS="-Duser.home=/zap/wrk" \
    -v "$REPORT_DIR:/zap/wrk:rw" \
    ghcr.io/zaproxy/zaproxy:stable \
    -c 'set -e; exec /zap/zap-baseline.py \
        -t "$1" \
        -m 2 \
        -r zap-report.html \
        -J zap-report.json \
        -w zap-report.md \
        -I' \
    bash "$APP_URL"

echo "Verifying generated DAST reports..."

test -s "$REPORT_DIR/zap-report.html"
test -s "$REPORT_DIR/zap-report.json"
test -s "$REPORT_DIR/zap-report.md"

echo "Post-deployment DAST scan completed successfully"
