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
  if [[ -n "${ANCLORA_DEFAULT_API_TOKEN:-}" ]]; then
    export ANCLORA_API_TOKENS="${ANCLORA_DEFAULT_API_TOKEN}"
    export ANCLORA_API_TOKEN="${ANCLORA_DEFAULT_API_TOKEN}"
    echo "[WARN] No se definieron ANCLORA_API_TOKENS ni ANCLORA_JWT_SECRET; se usará el token por defecto." >&2
  else
    echo "[ERROR] Debes definir ANCLORA_API_TOKENS, ANCLORA_JWT_SECRET o ANCLORA_DEFAULT_API_TOKEN antes de iniciar los servicios." >&2
    exit 1
  fi
fi

docker-compose up -d "$@"
