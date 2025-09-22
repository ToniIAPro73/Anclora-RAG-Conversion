#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

if [[ -z "${ANCLORA_API_TOKENS:-}" && -z "${ANCLORA_JWT_SECRET:-}" ]]; then
  echo "[ERROR] Debes definir ANCLORA_API_TOKENS o ANCLORA_JWT_SECRET antes de iniciar los servicios." >&2
  exit 1
fi

docker compose "$@" up -d
