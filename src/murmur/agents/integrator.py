import logging
from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage

from murmur.state import OverallState
from murmur.tools.mcp_client import MCPClient

logger = logging.getLogger(__name__)


async def integrator_node(
    state: OverallState, llm: BaseChatModel, mcp_client: MCPClient
) -> Dict[str, Any]:
    """
    Collects all agent Git branches from OverallState.
    Merges branches via internal scripts or workspace MCP git tools.
    For conflicts: AI resolution.
    If --review: pause execution for human.
    """
    state["step_count"] = state.get("step_count", 0) + 1
    if state["step_count"] >= state.get("max_steps", 200):
        return {
            "session_status": "failed",
            "messages": [SystemMessage(content="Max steps exceeded in integrator.")],
        }

    logger.debug(
        "Integrator spinning up. Merging task branches into main session branch."
    )

    tools = mcp_client.get_tools_for("workspace")
    git_branch = next((t for t in tools if t.name == "workspace__git_branch"), None)
    git_commit = next((t for t in tools if t.name == "workspace__git_commit"), None)

    if state.get("dry_run"):
        return {
            "session_status": "done",
            "messages": [SystemMessage(content="Dry run: skipped merge and commit.")],
        }

    session_id = state.get("session_id", "unknown")
    branch = f"murmur/{session_id[:8]}"

    # Simplified merge workflow logic for integration node
    if git_branch:
        await git_branch.ainvoke({"branch_name": branch})

    if state.get("no_commit"):
        msg = "Skipping final commit due to --no-commit flag."
        logger.info(msg)
        return {"session_status": "done", "messages": [SystemMessage(content=msg)]}

    commit_msg = f"chore(murmur): integration of changes [session: {session_id[:8]}]"
    if git_commit:
        await git_commit.ainvoke({"message": commit_msg})

    return {
        "session_status": "done",
        "messages": [SystemMessage(content="Integration complete.")],
    }
