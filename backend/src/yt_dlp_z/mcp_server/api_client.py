from typing import Any

import httpx2
from fastapi import FastAPI
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError


def _error_message(response: httpx2.Response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    return str(detail or f"yt-dlp-z answered with status {response.status_code}")


class ApiClient:
    """Calls this app's own REST API in-process, as the caller.

    Tools go through the API rather than the services so they get the same validation,
    path checks and auth as the web app, and can't drift from it."""

    def __init__(self, app: FastAPI) -> None:
        self._transport = httpx2.ASGITransport(app=app)

    async def call(
        self,
        ctx: Context,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        headers = {}
        authorization = (ctx.headers or {}).get("authorization")
        if authorization:
            headers["authorization"] = authorization
        # No timeout: link checks and yt-dlp updates take as long as they take.
        async with httpx2.AsyncClient(
            transport=self._transport, base_url="http://yt-dlp-z", timeout=None
        ) as client:
            response = await client.request(method, path, json=body, params=params, headers=headers)
        if response.is_error:
            raise ToolError(_error_message(response))
        if response.status_code == httpx2.codes.NO_CONTENT:
            return None
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text
