#!/usr/bin/env bash
# Generate self-signed TLS certs for local development
set -euo pipefail

CERT_DIR="${1:-./.certs}"
mkdir -p "$CERT_DIR"

if [ -f "$CERT_DIR/tls.crt" ] && [ -f "$CERT_DIR/tls.key" ]; then
    echo "Certificates already exist at $CERT_DIR"
    exit 0
fi

echo "Generating self-signed certificates in $CERT_DIR..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$CERT_DIR/tls.key" \
    -out "$CERT_DIR/tls.crt" \
    -subj "/C=AE/ST=Dubai/L=Dubai/O=AgenticAIOPs/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:host.docker.internal,IP:127.0.0.1"

echo "Done:"
echo "  $CERT_DIR/tls.crt"
echo "  $CERT_DIR/tls.key"
