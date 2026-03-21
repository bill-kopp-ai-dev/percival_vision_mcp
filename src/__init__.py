"""
Percival Vision MCP Server
A Model Context Protocol server for computer vision provider-agnostic
"""

__version__ = "1.0.0"
__author__ = "Nanobot Contributors"

from .server import PercivalVisionServer, main
from .config import Config

__all__ = [
    "PercivalVisionServer",
    "Config",
    "main"
]
