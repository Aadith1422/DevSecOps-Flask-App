
echo "Running OWASP ZAP baseline scan..."

docker run --rm \
    --network "$ZAP_NETWORK" \
    --user "$(id -u):$(id -g)" \
    --workdir /zap/wrk \
    --entrypoint /bin/bash \
    -e HOME=/zap/wrk \
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

echo "Checking generated ZAP reports..."

test -s "$REPORT_DIR/zap-report.html"
test -s "$REPORT_DIR/zap-report.json"
test -s "$REPORT_DIR/zap-report.md"

echo "OWASP ZAP baseline scan completed"
