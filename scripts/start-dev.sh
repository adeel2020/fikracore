#!/usr/bin/env bash
set -euo pipefail

echo "Starting AgenticAIOPs development environment..."

# Start infrastructure via Docker Compose
echo "[1/3] Starting infra (Postgres, Qdrant, Redis)..."
docker compose -f deploy/ci/docker-compose.ci.yaml up -d

# Start agents service
echo "[2/3] Starting agents service on :8001..."
PYTHONPATH=services/agents/src \
  uvicorn services.agents.src.main:app \
    --host 0.0.0.0 --port 8001 --reload \
    --reload-dir services/agents/src \
    --reload-dir shared/agenticaiops_shared &
AGENTS_PID=$!

echo "[3/3] Starting NGINX gateway on :8080 / :8443..."
docker run --rm --name agenticaiops-gateway \
  -p 8080:8080 -p 8443:8443 \
  -v "$PWD/services/gateway/nginx.conf:/etc/nginx/nginx.conf:ro" \
  nginx:alpine &
GATEWAY_PID=$!

echo ""
echo "=== Development environment running ==="
echo "  Gateway (HTTP)  : http://localhost:8080"
echo "  Gateway (HTTPS) : https://localhost:8443"
echo "  Agents API      : http://localhost:8001"
echo "  Health check    : http://localhost:8080/health"
echo "  Postgres        : localhost:5432"
echo "  Qdrant          : localhost:6333"
echo "  Redis           : localhost:6379"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $AGENTS_PID 2>/dev/null; docker stop agenticaiops-gateway 2>/dev/null; docker compose -f deploy/ci/docker-compose.ci.yaml down; echo 'Stopped.'" EXIT
wait
