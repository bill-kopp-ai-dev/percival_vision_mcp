#!/usr/bin/env python3
"""
Ollama Vision MCP Server
A Model Context Protocol server providing computer vision capabilities
"""

import asyncio
import base64
import json
import logging
import os
import sys
import mimetypes
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path
from openai import AsyncOpenAI

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .config import Config

# Configuração básica de log para ajudar no debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 1. Variáveis de Ambiente do Percival
# O fallback é a OpenAI, mas no seu nanobot você passará a URL do Venice.ai!
PERCIVAL_BASE_URL = os.getenv("PERCIVAL_BASE_URL", "https://api.openai.com/v1")
PERCIVAL_API_KEY = os.getenv("PERCIVAL_API_KEY")
PERCIVAL_DEFAULT_MODEL = os.getenv("PERCIVAL_DEFAULT_MODEL", "qwen32b-vision")

# 2. Validação Fail-Fast
# Se a chave não existir, o servidor nem deve iniciar para evitar erros silenciosos depois.
if not PERCIVAL_API_KEY:
    msg = "ERRO FATAL: A variável de ambiente PERCIVAL_API_KEY não foi configurada."
    logger.error(msg)
    raise ValueError(msg)

# 3. Instância Única do Cliente OpenAI (Agnóstico)
# Este 'percival_client' será a nossa ponte de comunicação universal.
percival_client = AsyncOpenAI(
    api_key=PERCIVAL_API_KEY,
    base_url=PERCIVAL_BASE_URL
)

logger.info(f"👁️ Percival Vision Engine inicializado! Apontando para: {PERCIVAL_BASE_URL}")

def encode_image_for_vision(image_path: str) -> dict:
    """
    Lê uma imagem local e retorna um dicionário com o base64 e o formato Data URI
    exigido pelo padrão OpenAI/Venice.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagem não encontrada no caminho: {image_path}")

    # Descobrir o MIME type (fallback para jpeg se falhar)
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"

    with open(image_path, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode('utf-8')
        
    # Retorna exatamente o formato que a API espera
    return {
        "mime_type": mime_type,
        "base64": base64_data,
        "data_uri": f"data:{mime_type};base64,{base64_data}"
    }

async def _process_vision_request(image_path: str, prompt: str, model: str = None) -> str:
    """
    Constrói o payload multimodal padrão da indústria e envia para o provedor.
    """
    target_model = model or PERCIVAL_DEFAULT_MODEL
    
    try:
        image_data = encode_image_for_vision(image_path)
        
        # Este é o "Maior Desafio" resolvido: O Payload Padrão!
        response = await percival_client.chat.completions.create(
            model=target_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data["data_uri"]
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500 # Mantemos um limite seguro para evitar estourar o contexto
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Erro na inferência visual: {str(e)}")
        return f"Falha ao processar a imagem com o modelo {target_model}: {str(e)}"

class PercivalVisionServer:
    def __init__(self):
        # Inicializa o Server MCP
        self.server = Server("percival-vision-mcp")
        self.config = Config()
        
        # Atribui o cliente global à instância do servidor
        self.client = percival_client
        self.default_model = PERCIVAL_DEFAULT_MODEL
        
        # Register handlers
        self.setup_handlers()
        
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List all available tools"""
            return [
                types.Tool(
                    name="list_available_vision_models",
                    description="Lista os modelos disponíveis no provedor atual. O LLM DEVE chamar esta função antes de usar outras ferramentas de imagem, caso não saiba exatamente qual modelo de VISÃO utilizar.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="analyze_image",
                    description="Analisa uma imagem baseada em um prompt específico fornecido pelo usuário.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_path": {
                                "type": "string",
                                "description": "Caminho local absoluto da imagem"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "Instrução opcional para análise"
                            },
                            "model": {
                                "type": "string",
                                "description": "Opcional. Nome do modelo de visão a ser usado. Se não souber, use a ferramenta list_available_vision_models primeiro."
                            }
                        },
                        "required": ["image_path"]
                    }
                ),
                types.Tool(
                    name="describe_image",
                    description="Gera uma descrição geral e detalhada de uma imagem.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_path": {
                                "type": "string",
                                "description": "Caminho local absoluto da imagem"
                            },
                            "model": {
                                "type": "string",
                                "description": "Opcional. Nome do modelo de visão a ser usado. Se não souber, use a ferramenta list_available_vision_models primeiro."
                            }
                        },
                        "required": ["image_path"]
                    }
                ),
                types.Tool(
                    name="identify_objects",
                    description="Identifica e lista os objetos presentes em uma imagem.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_path": {
                                "type": "string",
                                "description": "Caminho local absoluto da imagem"
                            },
                            "model": {
                                "type": "string",
                                "description": "Opcional. Nome do modelo de visão a ser usado. Se não souber, use a ferramenta list_available_vision_models primeiro."
                            }
                        },
                        "required": ["image_path"]
                    }
                ),
                types.Tool(
                    name="read_text",
                    description="Extrai textos de uma imagem (função de OCR).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_path": {
                                "type": "string",
                                "description": "Caminho local absoluto da imagem"
                            },
                            "model": {
                                "type": "string",
                                "description": "Opcional. Nome do modelo de visão a ser usado. Se não souber, use a ferramenta list_available_vision_models primeiro."
                            }
                        },
                        "required": ["image_path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str,
            arguments: Optional[Dict[str, Any]] = None
        ) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool execution"""
            try:
                if name == "list_available_vision_models":
                    try:
                        response = await percival_client.models.list()
                        all_models = [model.id for model in response.data]
                        
                        if not all_models:
                            result = "Nenhum modelo retornado pela API do provedor."
                        else:
                            vision_keywords = ["vision", "vl", "llava", "pixtral", "qwen"]
                            vision_models = [
                                m for m in all_models 
                                if any(kw in m.lower() for kw in vision_keywords)
                            ]
                            
                            if vision_models:
                                result = "👁️ Modelos de VISÃO detectados/recomendados:\n- " + "\n- ".join(vision_models)
                                result += "\n\n(Se nenhum destes funcionar, tente o modelo padrão configurado ou verifique a documentação do provedor)."
                            else:
                                result = "Catálogo completo de modelos (escolha um com suporte a visão):\n- " + "\n- ".join(all_models)
                                
                    except Exception as e:
                        logger.error(f"Erro ao listar modelos: {str(e)}")
                        result = f"Erro de conexão ao listar modelos. O provedor pode estar indisponível: {str(e)}"
                        
                    return [types.TextContent(type="text", text=result)]
                
                if not arguments:
                    raise ValueError("No arguments provided")
                
                image_path = arguments.get("image_path")
                if not image_path:
                    raise ValueError("image_path is required")
                
                # A nova função _process_vision_request já lida com o MIME do image_path local                
                # Call the appropriate tool via the routing logic
                if name == "analyze_image":
                    prompt = arguments.get("prompt", "Describe this image in detail")
                    model = arguments.get("model")
                    result = await _process_vision_request(image_path, prompt, model)
                    
                elif name == "describe_image":
                    prompt = "Descreva esta imagem em detalhes. O que você vê? Quais são os elementos principais, cores e o contexto geral?"
                    result = await _process_vision_request(image_path, prompt, arguments.get("model"))
                    
                elif name == "identify_objects":
                    prompt = "Liste todos os objetos distintos que você consegue identificar nesta imagem. Retorne a resposta preferencialmente em tópicos estruturados."
                    result = await _process_vision_request(image_path, prompt, arguments.get("model"))
                    
                elif name == "read_text":
                    prompt = "Extraia todo o texto visível nesta imagem. Retorne APENAS o texto extraído, mantendo a formatação e quebras de linha o mais fiel possível ao original."
                    result = await _process_vision_request(image_path, prompt, arguments.get("model"))
                    
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [types.TextContent(type="text", text=result)]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                error_msg = f"Error: {str(e)}"
                return [types.TextContent(type="text", text=error_msg)]
    
    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="percival-vision-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )

def main():
    """Main entry point"""
    try:
        server = PercivalVisionServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
