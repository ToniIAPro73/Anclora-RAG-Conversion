"""Utility helpers to export Prometheus metrics and Grafana dashboards."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _fetch(url: str, headers: Optional[Mapping[str, str]] = None) -> bytes:
    request = Request(url, headers=headers or {})
    with urlopen(request) as response:  # nosec: trusted internal endpoints
        return response.read()


def export_prometheus(url: str, output: Path) -> None:
    """Download the raw metrics payload exposed by a Prometheus endpoint."""

    payload = _fetch(url)
    output.write_bytes(payload)


def export_grafana(url: str, dashboard_uid: str, output: Path, api_key: str | None = None) -> None:
    """Export a Grafana dashboard as JSON using the public HTTP API."""

    endpoint = f"{url.rstrip('/')}/api/dashboards/uid/{dashboard_uid}"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = _fetch(endpoint, headers=headers)
    data = json.loads(payload.decode("utf-8"))
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prometheus-url", help="Endpoint HTTP que expone métricas en formato Prometheus")
    parser.add_argument("--grafana-url", help="URL base del servidor de Grafana")
    parser.add_argument("--dashboard-uid", help="UID del dashboard a exportar desde Grafana")
    parser.add_argument("--grafana-api-key", help="Token API para acceder a Grafana (opcional)")
    parser.add_argument("--output", required=True, help="Ruta del archivo de salida")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    tasks = [bool(args.prometheus_url), bool(args.grafana_url)]
    if tasks.count(True) != 1:
        raise SystemExit("Debe especificar únicamente --prometheus-url o --grafana-url")

    try:
        if args.prometheus_url:
            export_prometheus(args.prometheus_url, output_path)
        else:
            if not args.dashboard_uid:
                raise SystemExit("Para exportar desde Grafana se requiere --dashboard-uid")
            export_grafana(args.grafana_url, args.dashboard_uid, output_path, api_key=args.grafana_api_key)
    except (HTTPError, URLError) as exc:  # pragma: no cover - network errors
        raise SystemExit(f"No fue posible completar la exportación: {exc}") from exc

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
