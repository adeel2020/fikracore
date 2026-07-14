#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-latest}"
REGISTRY="${2:-ghcr.io/agenticaiops}"

echo "Building AgenticAIOPs images (version=$VERSION, registry=$REGISTRY)"

echo "[1/2] Building Gateway..."
docker build -t "$REGISTRY/gateway:$VERSION" -f services/gateway/Dockerfile services/gateway
docker tag "$REGISTRY/gateway:$VERSION" "$REGISTRY/gateway:latest"

echo "[2/2] Building Agents..."
docker build -t "$REGISTRY/agents:$VERSION" -f services/agents/Dockerfile .
docker tag "$REGISTRY/agents:$VERSION" "$REGISTRY/agents:latest"

echo "Done. Images:"
echo "  $REGISTRY/gateway:$VERSION"
echo "  $REGISTRY/agents:$VERSION"
