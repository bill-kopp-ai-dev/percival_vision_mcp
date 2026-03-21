"""
Configuration management for Percival Vision MCP Server
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the Percival Vision MCP server"""
    
    def __init__(self):
        # O Percival é agnóstico. Se não passar base_url, cai pro padrão OpenAI.
        self.base_url = os.getenv("PERCIVAL_BASE_URL", "https://api.openai.com/v1")
        self.api_key = os.getenv("PERCIVAL_API_KEY")
        self.default_model = os.getenv("PERCIVAL_DEFAULT_MODEL", "qwen32b-vision") # Exemplo de modelo do Venice
        
        self.log_level = os.getenv("PERCIVAL_LOG_LEVEL", "INFO")
        self.timeout = int(os.getenv("PERCIVAL_TIMEOUT", "120"))
        
        # Apply log level
        logging.getLogger().setLevel(getattr(logging, self.log_level.upper()))
