import argparse
import asyncio
import json
import logging
import os
import hmac
from typing import Sequence
from ipaddress import ip_address

from server import configure_runtime_settings, mcp
from utils.nanobot_profile import CONTRACT_VERSION, SERVER_NAME, build_nanobot_profile
from utils.config import JARVINA_BASE_URL, JARVINA_VISION_MODEL

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import uvicorn

# Import tools for registration side effects
import tools.vision_tools  # noqa: F401

logger = logging.getLogger(__name__)

def _is_loopback_host(host: str) -> bool:
    normalized_host = host.strip().lower()
    if normalized_host in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ip_address(normalized_host).is_loopback
    except ValueError:
        return False

class BearerTokenAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str):
        super().__init__(app)
        self._token = token.strip()

    async def dispatch(self, request: Request, call_next):
        provided_token = ""
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            provided_token = auth_header[7:].strip()
        elif "x-mcp-auth-token" in request.headers:
            provided_token = request.headers["x-mcp-auth-token"].strip()

        if not provided_token or not hmac.compare_digest(provided_token, self._token):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)

async def _run_http_transport(mode: str, host: str, port: int, log_level: str, mount_path: str, auth_token: str | None):
    if mode == "sse":
        app = mcp.sse_app(mount_path=mount_path)
    else:
        app = mcp.streamable_http_app()

    if auth_token:
        app.add_middleware(BearerTokenAuthMiddleware, token=auth_token)

    config = uvicorn.Config(app, host=host, port=port, log_level=log_level.lower())
    server = uvicorn.Server(config)
    await server.serve()

def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Percival Vision MCP Server (Async)")
    parser.add_argument("--mode", choices=("stdio", "sse", "streamable-http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--mount-path", default="/")
    parser.add_argument("--print-profile", action="store_true")

    args = parser.parse_args(argv)

    if args.print_profile:
        print(json.dumps({
            "server": SERVER_NAME,
            "contract_version": CONTRACT_VERSION,
            "profile": build_nanobot_profile()
        }, indent=2))
        return

    # Basic setup
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(levelname)s: %(message)s")
    
    configure_runtime_settings(
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        mount_path=args.mount_path
    )

    token = os.getenv("PERCIVAL_VISION_MCP_AUTH_TOKEN")
    
    logger.info(f"Starting {SERVER_NAME} in {args.mode} mode...")
    logger.info(f"Base URL: {JARVINA_BASE_URL} | Model: {JARVINA_VISION_MODEL}")

    if args.mode == "stdio":
        mcp.run(transport="stdio")
    else:
        asyncio.run(_run_http_transport(args.mode, args.host, args.port, args.log_level, args.mount_path, token))

if __name__ == "__main__":
    main()
