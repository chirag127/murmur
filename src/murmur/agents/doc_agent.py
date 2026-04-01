from langchain_core.language_models import BaseChatModel
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from murmur.agents.tools import claim_file, release_file
from murmur.tools.mcp_client import MCPClient


def build_doc_team(
    llm: BaseChatModel, mcp_client: MCPClient, memory_manager
) -> CompiledGraph:
    """Builds the Documentation Subgroup."""

    worker_tools = mcp_client.get_tools_for_role("doc_worker")
    worker_tools.extend([claim_file, release_file])

    doc_analyst = create_react_agent(
        model=llm,
        tools=worker_tools,
        name="doc_analyst",
        prompt="""You are the doc_analyst.
        Read the source files and existing docs.""",
    )

    doc_writer = create_react_agent(
        model=llm,
        tools=worker_tools,
        name="doc_writer",
        prompt="""You are the doc_writer.
        Write or update docstrings and README sections.
        Use tavily/linkup for doc research if required. Claim files before editing.""",
    )

    doc_team = create_supervisor(
        agents=[doc_analyst, doc_writer],
        model=llm,
        prompt="""You are the documentation supervisor.
        Coordinate reading code logic and writing accurate documentation.""",
    )

    return doc_team.compile(name="doc_team")
