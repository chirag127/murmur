from langchain_core.language_models import BaseChatModel
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from murmur.agents.tools import claim_file, release_file, run_shell, run_tests
from murmur.tools.mcp_client import MCPClient


def build_refactor_team(
    llm: BaseChatModel, mcp_client: MCPClient, memory_manager
) -> CompiledGraph:
    """Builds the Refactor Subgroup."""

    worker_tools = mcp_client.get_tools_for_role("refactor_worker")
    worker_tools.extend([claim_file, release_file, run_shell, run_tests])

    refactor_analyst = create_react_agent(
        model=llm,
        tools=worker_tools,
        name="refactor_analyst",
        prompt="""You are the Murmur refactor_analyst.
        Read files and plan edits. Use ref/context7/docfork for library docs before using them.
        Use sequential-thinking before making any decisions.""",
    )

    refactor_writer = create_react_agent(
        model=llm,
        tools=worker_tools,
        name="refactor_writer",
        prompt="""You are the Murmur refactor_writer.
        Claim files, write changes via workspace tools, then release files.
        Use sequential-thinking before editing. Always lock files.""",
    )

    refactor_verifier = create_react_agent(
        model=llm,
        tools=worker_tools,
        name="refactor_verifier",
        prompt="""You are the Murmur refactor_verifier.
        Run linter and tests. Fix if needed.""",
    )

    refactor_team = create_supervisor(
        agents=[refactor_analyst, refactor_writer, refactor_verifier],
        model=llm,
        prompt="""You are the refactor team supervisor.
        Delegate to analyst, then writer, then verifier.
        Finish when verification passes.""",
    )

    return refactor_team.compile(name="refactor_team")
