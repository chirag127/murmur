import functools
from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph

from murmur.state import OverallState
from murmur.agents.planner import planner_node
from murmur.agents.router import router_node
from murmur.agents.integrator import integrator_node
from murmur.agents.reviewer import review_agent_node
from murmur.agents.refactor import build_refactor_team
from murmur.agents.test_agent import build_test_team
from murmur.agents.doc_agent import build_doc_team

from murmur.tools.mcp_client import MCPClient
from murmur.memory.manager import MemoryManager


def build_graph(llm, mcp_client: MCPClient, memory: MemoryManager) -> CompiledGraph:
    """
    Constructs the Supervisor pattern StateGraph combining all nodes, routers, and sub-graphs.
    """
    builder = StateGraph(OverallState)
    
    # 1. Provide dependencies explicitly using functools
    planner = functools.partial(planner_node, llm=llm, mcp_client=mcp_client)
    integrator = functools.partial(integrator_node, llm=llm, mcp_client=mcp_client)
    review = functools.partial(review_agent_node, llm=llm, mcp_client=mcp_client)
    
    # 2. Add Top-Level Nodes
    builder.add_node("planner_node", planner)
    builder.add_node("router_node", router_node)
    builder.add_node("integrator", integrator)
    builder.add_node("review_agent", review)

    # 3. Add Sub-graph Teams
    builder.add_node("refactor_team", build_refactor_team(llm, mcp_client, memory))
    builder.add_node("test_team", build_test_team(llm, mcp_client, memory))
    builder.add_node("doc_team", build_doc_team(llm, mcp_client, memory))
    
    # 4. Define graph transitions
    builder.add_edge(START, "planner_node")
    builder.add_edge("planner_node", "router_node")
    
    # (Router natively dispatches the graph via LangGraph Command)
    # So we don't explicitly declare outgoing conditional edge objects for Router!
    
    # Worker groups loop back to router after finishing their sub-task
    builder.add_edge("refactor_team", "router_node")
    builder.add_edge("test_team", "router_node")
    builder.add_edge("doc_team", "router_node")
    builder.add_edge("review_agent", "router_node")
    
    # Eventually going to integrator
    builder.add_edge("integrator", END)
    
    return builder.compile(checkpointer=memory.checkpointer, store=memory.store, name="murmur")
