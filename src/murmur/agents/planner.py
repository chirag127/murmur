import json
import logging
from typing import Dict, Any, List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseChatModel

from murmur.state import OverallState, TaskSpec, TaskStatus
from murmur.tools.mcp_client import MCPClient

logger = logging.getLogger(__name__)


async def planner_node(
    state: OverallState,
    llm: BaseChatModel,
    mcp_client: MCPClient
) -> Dict[str, Any]:
    """
    Analyzes the task and produces structured Plan output.
    Writes TaskSpec list to the state.
    """
    state["step_count"] = state.get("step_count", 0) + 1
    if state["step_count"] >= state.get("max_steps", 200):
        return {"session_status": "failed", "messages": [SystemMessage(content="Max steps exceeded in planner.")]}

    logger.debug("Planner node starting...")
    task_desc = state["task"]
    repo_path = state["repo_path"]

    # Gather available tools
    tools = mcp_client.get_tools_for_role("planner")
    
    # Simple direct planning prompt.
    prompt = f"""
    You are the Murmur Planner.
    Analyze the following task and construct a JSON list of sub-tasks.
    Each sub-task must conform to this schema:
    [
      {{
        "id": "task_1",
        "title": "Short title",
        "description": "Detailed explanation",
        "target_paths": [".\\path\\to\\file"],
        "depends_on": [],
        "agent_type": "refactor" // "refactor"|"test"|"doc"|"review"
      }}
    ]
    
    TASK: {task_desc}
    REPO PATH: {repo_path}
    
    Output ONLY valid JSON inside a ```json``` block.
    """

    response = await llm.ainvoke([SystemMessage(content=prompt)])
    content = response.content
    
    tasks: List[TaskSpec] = []
    
    try:
        # Extract json array
        if "```json" in content:
            raw = content.split("```json")[1].split("```")[0].strip()
        else:
            raw = content.strip()
            
        json_tasks = json.loads(raw)
        for t in json_tasks:
            spec = TaskSpec(
                id=t["id"],
                title=t["title"],
                description=t["description"],
                target_paths=t.get("target_paths", []),
                depends_on=t.get("depends_on", []),
                agent_type=t.get("agent_type", "refactor")
            )
            tasks.append(spec)
    except Exception as e:
        logger.error(f"Planner JSON parsing failed: {e}. Fallback to string payload.")
        tasks.append(TaskSpec(
            id="task_1",
            title="Execute user task",
            description=task_desc,
            agent_type="refactor"
        ))

    # Try creating branch unless dry_run
    if not state.get("dry_run"):
        branch_name = f"murmur/{state['session_id'][:8]}"
        workspace_tools = mcp_client.get_tools_for("workspace")
        branch_tool = next((t for t in workspace_tools if t.name == "workspace__git_branch"), None)
        if branch_tool:
            await branch_tool.ainvoke({"branch_name": branch_name})
            
    return {"tasks": tasks, "next_agent": "router"}
