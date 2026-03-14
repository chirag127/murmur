from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_core.language_models import BaseChatModel

from murmur.tools.mcp_client import MCPClient
from murmur.agents.tools import claim_file, release_file, run_shell, run_tests


def build_test_team(llm: BaseChatModel, mcp_client: MCPClient, memory_manager) -> CompiledGraph:
    """Builds the Test Subgroup."""
    
    worker_tools = mcp_client.get_tools_for_role("test_worker")
    worker_tools.extend([claim_file, release_file, run_shell, run_tests])
    
    test_analyst = create_react_agent(
        model=llm,
        tools=mcp_client.get_tools_for_role("test_worker"),
        name="test_analyst",
        prompt="""You are the test_analyst.
        Read the source files and any existing test files. 
        Use ref for testing library documentation."""
    )
    
    test_writer = create_react_agent(
        model=llm,
        tools=worker_tools,
        name="test_writer",
        prompt="""You are the test_writer.
        Write new test files. Claim before writing, release after."""
    )
    
    test_runner = create_react_agent(
        model=llm,
        tools=worker_tools,
        name="test_runner",
        prompt="""You are the test_runner.
        Run pytest. If tests fail, read errors, fix, and retry (up to 3x)."""
    )
    
    test_team = create_supervisor(
        agents=[test_analyst, test_writer, test_runner],
        model=llm,
        prompt="""You are the test team supervisor.
        Coordinate analyzing code, writing tests, and running them."""
    )
    
    return test_team.compile(name="test_team")
