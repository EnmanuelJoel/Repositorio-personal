"""HTTP client for Automox REST API."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional
import time

import requests


class AutomoxAPIError(RuntimeError):
    """Base exception for Automox API failures."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AutomoxAuthError(AutomoxAPIError):
    """Raised when authentication fails."""


class AutomoxRateLimitError(AutomoxAPIError):
    """Raised when Automox returns HTTP 429."""


@dataclass
class AutomoxAPIClient:
    api_key: str
    org_id: int
    base_url: str = "https://console.automox.com/api"
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        if not self.session:
            self.session = requests.Session()

    # -- public endpoints -------------------------------------------------
    def get_devices(self, limit: int = 500) -> List[Dict]:
        return list(self._get_paginated("/servers", limit=limit, params={"include_server_events": 1}))

    def get_policies(self, limit: int = 500) -> List[Dict]:
        return list(self._get_paginated("/policies", limit=limit))

    def get_groups(self, limit: int = 500) -> List[Dict]:
        return list(self._get_paginated("/servergroups", limit=limit))

    def get_software(self, limit: int = 500) -> List[Dict]:
        return list(self._get_paginated(f"/orgs/{self.org_id}/packages", limit=limit))

    def get_events(self, start: str, end: str, limit: int = 500) -> List[Dict]:
        params = {"startDate": start, "endDate": end}
        return list(self._get_paginated("/events", limit=limit, params=params))

    # -- helpers ----------------------------------------------------------
    def _get_paginated(self, path: str, *, limit: int = 500, params: Optional[Dict] = None) -> Iterable[Dict]:
        page = 0
        while True:
            page_params = dict(params or {})
            page_params.update({"page": page, "limit": limit})
            payload = self._request("GET", path, params=page_params)
            if not isinstance(payload, list):
                break
            for row in payload:
                yield row
            if len(payload) < limit:
                break
            page += 1

    def _request(self, method: str, path: str, **kwargs) -> Dict | List:
        assert self.session is not None
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.setdefault("Authorization", f"Bearer {self.api_key}")
        headers.setdefault("User-Agent", "AutomoxDashboard/1.0")
        params = kwargs.pop("params", {})
        params.setdefault("o", self.org_id)
        response = self.session.request(method, url, headers=headers, params=params, timeout=30, **kwargs)
        if response.status_code == 401:
            raise AutomoxAuthError("Error de autenticación con Automox", status_code=401)
        if response.status_code == 404:
            raise AutomoxAPIError("Organización no encontrada", status_code=404)
        if response.status_code == 429:
            retry = int(response.headers.get("Retry-After", "1"))
            raise AutomoxRateLimitError(f"Límite de solicitudes excedido. Reintenta en {retry}s", status_code=429)
        if response.status_code >= 500:
            raise AutomoxAPIError("Error interno en Automox", status_code=response.status_code)
        if not response.ok:
            raise AutomoxAPIError(f"Error al llamar a Automox ({response.status_code})", status_code=response.status_code)
        try:
            return response.json()
        except ValueError as exc:
            raise AutomoxAPIError("Respuesta JSON inválida") from exc
