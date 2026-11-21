#!/usr/bin/env bash
set -euo pipefail

STAGING_CONTAINER="devsecops-flask-staging"
ZAP_NETWORK="devsecops-zap-staging-${BUILD_NUMBER:-local}"
REPORT_DIR="$(pwd)/zap-reports"
CONFIG_FILE="$(pwd)/scripts/zap-public.yaml"

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

echo "Checking ZAP configuration..."
test -s "$CONFIG_FILE"

echo "Creating ZAP scan network..."
docker network create "$ZAP_NETWORK"

echo "Connecting deployed staging application..."
docker network connect "$ZAP_NETWORK" "$STAGING_CONTAINER"

echo "Checking deployed staging application..."
docker exec "$STAGING_CONTAINER" \
    python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)"

echo "Running OWASP ZAP Automation Framework..."

# Remove old reports so a failed scan cannot reuse previous results.
rm -f \
    "$REPORT_DIR/zap-report.html" \
    "$REPORT_DIR/zap-report.json" \
    "$REPORT_DIR/zap-report.md"

docker run --rm \
    --network "$ZAP_NETWORK" \
    --user "$(id -u):$(id -g)" \
    --workdir /zap/wrk \
    --entrypoint /bin/bash \
    -e HOME=/zap/wrk \
    -e JAVA_TOOL_OPTIONS="-Duser.home=/zap/wrk" \
    -v "$REPORT_DIR:/zap/wrk:rw" \
    -v "$CONFIG_FILE:/zap/wrk/zap-public.yaml:ro" \
    ghcr.io/zaproxy/zaproxy:stable \
    -c 'set -e; exec /zap/zap.sh \
        -cmd \
        -autorun /zap/wrk/zap-public.yaml'

echo "Verifying generated DAST reports..."

test -s "$REPORT_DIR/zap-report.html"
test -s "$REPORT_DIR/zap-report.json"
test -s "$REPORT_DIR/zap-report.md"

echo "Post-deployment DAST scan completed successfully"