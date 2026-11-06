from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from flask import Flask, jsonify, render_template, request

from app.config import Settings
from app.services.dashboard_repository import DashboardRepository


def create_app(repository: DashboardRepository | None = None) -> Flask:
    app = Flask(__name__)
    settings = Settings()
    if repository is not None:
        app.config["DASHBOARD_REPOSITORY"] = repository
    elif settings.db_enabled:
        app.config["DASHBOARD_REPOSITORY"] = DashboardRepository(
            host=settings.db_host, port=settings.db_port, database=settings.db_database,
            user=settings.db_user, password=settings.db_password,
        )
    else:
        app.config["DASHBOARD_REPOSITORY"] = None

    @app.get("/")
    def index():
        return render_template("dashboard.html")

    @app.get("/api/resumen")
    def summary():
        return _run_query(app, lambda repo: repo.summary())

    @app.get("/api/expedientes")
    def expedientes():
        page, page_size = _pagination()
        return _run_query(app, lambda repo: repo.expedientes(
            page=page, page_size=page_size,
            search=request.args.get("buscar", "").strip()[:100],
            status=request.args.get("estado", "").strip().upper(),
        ))

    @app.get("/api/auditoria")
    def audit_logs():
        page, page_size = _pagination()
        return _run_query(app, lambda repo: repo.audit_logs(
            page=page, page_size=page_size,
            search=request.args.get("buscar", "").strip()[:100],
            status=request.args.get("estado", "").strip().upper(),
        ))

    return app


def _pagination() -> tuple[int, int]:
    page = max(request.args.get("pagina", 1, type=int) or 1, 1)
    page_size = request.args.get("limite", 10, type=int) or 10
    return page, min(max(page_size, 5), 100)


def _run_query(app: Flask, operation):
    repository = app.config.get("DASHBOARD_REPOSITORY")
    if repository is None:
        return jsonify({
            "error": "Base de datos no habilitada",
            "detail": "Configura DB_ENABLED=true y las credenciales de MariaDB para consultar la información.",
        }), 503
    try:
        return app.response_class(
            json.dumps(operation(repository), ensure_ascii=False, default=_json_default),
            mimetype="application/json",
        )
    except Exception:
        app.logger.exception("No fue posible consultar el tablero")
        return jsonify({
            "error": "No fue posible conectar con MariaDB",
            "detail": "Verifica que el servicio esté activo y que las credenciales sean correctas.",
        }), 503


def _json_default(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Tipo no serializable: {type(value).__name__}")


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
