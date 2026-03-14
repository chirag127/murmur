import logging
from typing import Dict, Any

from langchain_core.messages import SystemMessage
from langchain_core.language_models import BaseChatModel

from murmur.state import OverallState
from murmur.tools.mcp_client import MCPClient

logger = logging.getLogger(__name__)


async def review_agent_node(
    state: OverallState,
    llm: BaseChatModel,
    mcp_client: MCPClient
) -> Dict[str, Any]:
    """
    Code review of recent Git changes. Produces structured findings.
    Does NOT edit files.
    """
    state["step_count"] = state.get("step_count", 0) + 1
    if state["step_count"] >= state.get("max_steps", 200):
        return {"session_status": "failed", "messages": [SystemMessage(content="Max steps exceeded in reviewer.")]}

    logger.debug("Review Agent analyzing git diff...")
    
    workspace_tools = mcp_client.get_tools_for("workspace")
    git_diff_tool = next((t for t in workspace_tools if t.name == "workspace__git_diff"), None)
    diff = ""
    if git_diff_tool:
        diff_resp = await git_diff_tool.ainvoke({"path": "."})
        diff = diff_resp
        
    prompt = f"""
    You are the Murmur Review Agent.
    Review the following Git patch. Identify architecture risks, 
    incorrect typing, testing holes, and edge case bugs.
    
    <git_diff>
    {diff}
    </git_diff>
    
    Output a structured code review summary. Do not edit files.
    """
    
    response = await llm.ainvoke([SystemMessage(content=prompt)])
    
    # Normally we attach review to current task
    tasks = state.get("tasks", [])
    if state.get("current_task_id"):
        for t in tasks:
            if t.id == state["current_task_id"]:
                t.status = "done"
                t.result_summary = response.content
                break
                
    return {"tasks": tasks, "next_agent": "router"}
