#!/usr/bin/env bash
set -euo pipefail

# Local development deploy — runs the agents service and NGINX gateway locally
# Requires: python3.11+, docker (for NGINX only)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== AgenticAIOPs Local Dev ==="

# Determine upstream host for NGINX
if command -v docker &> /dev/null; then
    case "$(uname -s)" in
        Darwin) UPSTREAM_HOST="host.docker.internal" ;;
        Linux)  UPSTREAM_HOST="172.17.0.1" ;;
        *)      UPSTREAM_HOST="host.docker.internal" ;;
    esac
else
    UPSTREAM_HOST="127.0.0.1"
fi
UPSTREAM_PORT=${AGENTS_PORT:-8001}

# Generate TLS certs if needed
CERT_DIR="$REPO_ROOT/.certs"
if [ ! -f "$CERT_DIR/tls.crt" ]; then
    bash "$SCRIPT_DIR/gen-certs.sh" "$CERT_DIR"
fi

# Create a patched nginx.conf for local dev with Docker networking
NGINX_CONF_TMP=$(mktemp)
sed -e "s/server agents-service:8001/server $UPSTREAM_HOST:$UPSTREAM_PORT/" \
    -e "s|/etc/ssl/certs/tls.crt|/etc/nginx/certs/tls.crt|" \
    -e "s|/etc/ssl/certs/tls.key|/etc/nginx/certs/tls.key|" \
    "$REPO_ROOT/services/gateway/nginx.conf" > "$NGINX_CONF_TMP"

# 1. Shared library
echo "[1/4] Installing shared library..."
pip install -e "$REPO_ROOT/shared/agenticaiops_shared"

# 2. Install agents dependencies
echo "[2/4] Installing agents dependencies..."
pip install -e "$REPO_ROOT/services/agents"

# 3. Start agents service
echo "[3/4] Starting agents service on :$UPSTREAM_PORT..."
PYTHONPATH="$REPO_ROOT/services/agents/src" \
  uvicorn main:app --host 0.0.0.0 --port "$UPSTREAM_PORT" --reload \
    --reload-dir "$REPO_ROOT/services/agents/src" \
    --reload-dir "$REPO_ROOT/shared/agenticaiops_shared" &
AGENTS_PID=$!

# 4. Start NGINX gateway
echo "[4/4] Starting NGINX gateway on :8080 (:8443 HTTPS)..."
docker rm -f agenticaiops-gateway 2>/dev/null || true
docker run --name agenticaiops-gateway \
    --add-host host.docker.internal:host-gateway \
    -p 8080:8080 -p 8443:8443 \
    -v "$NGINX_CONF_TMP:/etc/nginx/nginx.conf:ro" \
    -v "$CERT_DIR:/etc/nginx/certs:ro" \
    nginx:1.27-alpine &
GATEWAY_PID=$!

echo "=== Running ==="
echo "  Agents API (direct) : http://localhost:$UPSTREAM_PORT"
echo "  Gateway (HTTP)      : http://localhost:8080"
echo "  Gateway (HTTPS)     : https://localhost:8443"
echo "  Health              : http://localhost:$UPSTREAM_PORT/health"
echo ""
echo "Press Ctrl+C to stop both."
echo ""

cleanup() {
    echo "Stopping..."
    kill $AGENTS_PID 2>/dev/null || true
    docker rm -f agenticaiops-gateway 2>/dev/null || true
    rm -f "$NGINX_CONF_TMP"
    echo "Stopped."
}
trap cleanup EXIT INT TERM
wait
