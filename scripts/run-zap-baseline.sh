
#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-devsecops-flask-app}"
BUILD_NUMBER="${BUILD_NUMBER:-latest}"

APP_CONTAINER="devsecops-flask-dast-${BUILD_NUMBER}"
ZAP_NETWORK="devsecops-zap-${BUILD_NUMBER}"
APP_URL="http://${APP_CONTAINER}:5000"

REPORT_DIR="$(pwd)/zap-reports"
mkdir -p "$REPORT_DIR"

cleanup() {
    echo "Cleaning up temporary containers..."
    docker rm -f "$APP_CONTAINER" >/dev/null 2>&1 || true
    docker network rm "$ZAP_NETWORK" >/dev/null 2>&1 || true
}

trap cleanup EXIT

echo "Creating Docker network..."
docker network create "$ZAP_NETWORK"

echo "Starting Flask application..."

docker run -d \
    --name "$APP_CONTAINER" \
    --network "$ZAP_NETWORK" \
    -e SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
    "${IMAGE_NAME}:${BUILD_NUMBER}"

echo "Waiting for Flask health check..."

HEALTHY=0

for i in $(seq 1 30); do
    if docker exec "$APP_CONTAINER" \
        python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)" \
        >/dev/null 2>&1; then
        HEALTHY=1
        break
    fi

    sleep 2
done

if [ "$HEALTHY" -ne 1 ]; then
    echo "Flask health check failed"
    docker logs "$APP_CONTAINER"
    exit 1
fi

echo "Flask health check passed"

echo "Running OWASP ZAP baseline scan..."

docker run --rm \
    --network "$ZAP_NETWORK" \
    --user "$(id -u):$(id -g)" \
    -v "$REPORT_DIR:/zap/wrk:rw" \
    ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py \
    -t "$APP_URL" \
    -m 2 \
    -r zap-report.html \
    -J zap-report.json \
    -w zap-report.md \
    -I

echo "OWASP ZAP baseline scan completed"

