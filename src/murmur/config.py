from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServerConfig(BaseModel):
    """Configuration for an individual MCP Server."""

    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    transport: str = "stdio"
    url: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    env: Dict[str, str] = Field(default_factory=dict)
    optional: bool = False
    description: str = ""


class AppConfig(BaseSettings):
    """
    Main application configuration.
    Resolves automatically from default -> .murmur/config.yaml -> environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LLM settings
    model: str = "nvidia:meta/llama-3.3-70b-instruct"
    temperature: float = 0.2
    max_tokens: int = 4096

    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    groq_api_key: str = ""
    openrouter_api_key: str = ""

    # Behavior
    repo_path: str = "."
    dry_run: bool = False
    max_workers: int = 4
    max_depth: int = 3
    auto_branch: bool = True
    auto_commit: bool = True
    no_commit: bool = False
    review_mode: bool = False

    # Memory / persistence
    db_path: str = ".murmur/murmur.db"
    memory_db_path: str = ".murmur/memory.db"
    snapshot_interval: int = 30

    # RAG
    rag_enabled: bool = True
    rag_backend: str = "chroma"
    rag_db_path: str = ".murmur/rag"

    # MCP server credentials
    linkup_api_key: str = ""
    exa_api_key: str = ""
    tavily_api_key: str = ""
    ref_api_key: str = ""
    context7_api_key: str = ""
    serper_api_key: str = ""
    docfork_api_key: str = ""
    brave_api_key: str = ""

    # Memory providers
    mem0_api_key: str = ""

    # Services
    github_personal_access_token: str = ""
    postgres_connection_string: str = ""

    # LangSmith / LangFuse Tracing
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False

    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"

    # Custom additions
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
