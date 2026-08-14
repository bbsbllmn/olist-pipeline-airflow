#!/usr/bin/env bash
# Base64-encodes the local GCP service-account key so it can be pasted into a
# CI/CD secret store (GitHub Actions secret, Composer environment variable,
# Secret Manager) without worrying about JSON escaping.
#
# Usage: ./scripts/encode-secret.sh ./keys/gcp-credentials.json
set -euo pipefail

KEY_FILE="${1:?Usage: encode-secret.sh <path-to-key.json>}"

if [[ ! -f "$KEY_FILE" ]]; then
  echo "File not found: $KEY_FILE" >&2
  exit 1
fi

base64 -i "$KEY_FILE" | tr -d '\n'
echo
