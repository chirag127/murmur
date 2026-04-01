import logging
from typing import Any, Dict, List

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from murmur.config import AppConfig

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Manages all MCP server connections and exposes tools as
    namespaced LangChain tools: <server>__<tool>
    e.g. workspace__read_file, exa__web_search_exa
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self._client: MultiServerMCPClient | None = None

        server_config: dict[str, Any] = {
            "workspace": {
                "transport": "stdio",
                "command": "python",
                "args": ["-m", "murmur.mcp_servers.workspace_mcp"],
            },
            "sequential-thinking": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
            },
        }

        if config.docfork_api_key or True:
            server_config["docfork"] = {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "docfork"],
            }

        if config.serper_api_key or config.tavily_api_key:
            server_config["kindly-web-search"] = {
                "transport": "stdio",
                "command": "uvx",
                "args": [
                    "--from",
                    "git+https://github.com/Shelpuk-AI-Technology-Consulting/kindly-web-search-mcp-server",
                    "kindly-web-search-mcp-server",
                    "start-mcp-server",
                ],
                "env": {
                    "SERPER_API_KEY": config.serper_api_key,
                    "TAVILY_API_KEY": config.tavily_api_key,
                    "SEARXNG_BASE_URL": "https://searxng.site/",
                    "GITHUB_TOKEN": "PASTE_GITHUB_TOKEN_OR_LEAVE_EMPTY",
                    "KINDLY_BROWSER_EXECUTABLE_PATH": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                },
            }

        if config.linkup_api_key:
            server_config["linkup"] = {
                "transport": "streamable_http",
                "url": f"https://mcp.linkup.so/mcp?apiKey={config.linkup_api_key}",
            }

        if config.exa_api_key:
            server_config["exa"] = {
                "transport": "streamable_http",
                "url": "https://mcp.exa.ai/mcp",
                "headers": {"x-api-key": config.exa_api_key},
            }

        if config.tavily_api_key:
            server_config["tavily"] = {
                "transport": "streamable_http",
                "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={config.tavily_api_key}",
            }

        if config.ref_api_key:
            server_config["ref"] = {
                "transport": "streamable_http",
                "url": "https://api.ref.tools/mcp",
                "headers": {"x-ref-api-key": config.ref_api_key},
            }

        if config.context7_api_key:
            server_config["context7"] = {
                "transport": "streamable_http",
                "url": "https://mcp.context7.com/mcp",
                "headers": {"CONTEXT7_API_KEY": config.context7_api_key},
            }

        for name, user_conf in config.mcp_servers.items():
            conf: Dict[str, Any] = {
                "transport": user_conf.transport,
            }
            if user_conf.transport == "stdio":
                conf["command"] = user_conf.command
                conf["args"] = user_conf.args
                conf["env"] = user_conf.env
            else:
                conf["url"] = user_conf.url
                conf["headers"] = user_conf.headers

            server_config[name] = conf

        self._server_config = server_config
        self._tools_cache: List[BaseTool] = []

    async def __aenter__(self) -> "MCPClient":
        logger.debug(
            f"Starting MultiServerMCPClient with servers: {list(self._server_config.keys())}"
        )
        self._client = MultiServerMCPClient(self._server_config)
        await self._client.__aenter__()
        # eagerly load tools
        self._tools_cache = await self._client.get_tools()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def get_all_tools(self) -> List[BaseTool]:
        if not self._client:
            raise RuntimeError("MCPClient not started. Use async with context.")
        return self._tools_cache

    def get_tools_for(self, server: str) -> List[BaseTool]:
        return [t for t in self._tools_cache if t.name.startswith(f"{server}__")]

    def get_tools_for_role(self, role: str) -> List[BaseTool]:
        """Principle of least privilege per agent role."""
        if not self._client:
            return []

        if role == "supervisor":
            allowed = ["workspace", "sequential-thinking", "context7", "ref", "docfork"]
        elif role == "planner":
            allowed = [
                "workspace",
                "sequential-thinking",
                "context7",
                "ref",
                "docfork",
                "exa",
                "tavily",
                "linkup",
            ]
        elif role == "refactor_worker":
            allowed = [
                "workspace",
                "sequential-thinking",
                "context7",
                "ref",
                "docfork",
                "exa",
                "tavily",
                "linkup",
                "kindly-web-search",
            ]
        elif role == "test_worker":
            allowed = ["workspace", "sequential-thinking", "context7", "ref"]
        elif role == "doc_worker":
            allowed = ["workspace", "sequential-thinking", "ref", "docfork", "tavily"]
        elif role == "review_agent":
            allowed = ["workspace", "sequential-thinking", "ref"]
        elif role == "integrator":
            allowed = ["workspace", "sequential-thinking"]
        else:
            allowed = ["workspace"]

        allowed_tools = []
        for t in self._tools_cache:
            server_name = t.name.split("__")[0]
            if server_name in allowed:
                # Disallow modifying files if read-only role
                if role in ("supervisor", "planner", "review_agent"):
                    if t.name in (
                        "workspace__write_file",
                        "workspace__create_patch",
                        "workspace__git_commit",
                    ):
                        continue
                allowed_tools.append(t)

        return allowed_tools
