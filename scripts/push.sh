#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-latest}"
REGISTRY="${2:-ghcr.io/agenticaiops}"

echo "Pushing images to $REGISTRY"
docker push "$REGISTRY/gateway:$VERSION"
docker push "$REGISTRY/gateway:latest"
docker push "$REGISTRY/agents:$VERSION"
docker push "$REGISTRY/agents:latest"
echo "Done."
