"""Thin HTTP API adapter connecting the Theseus localhost UI (`app/ui/`) to Argon's backend services."""
from __future__ import annotations

from app.api.server import TheseusLocalApplication, create_app_server, run_server

__all__ = ["TheseusLocalApplication", "create_app_server", "run_server"]
