import logging
from typing import Dict, Any
from langgraph.types import Command

from murmur.state import OverallState

logger = logging.getLogger(__name__)


async def router_node(state: OverallState) -> Command:
    """
    Finds next PENDING task where all depends_on are DONE.
    Marks task IN_PROGRESS and routes to target group subgraph.
    """
    state["step_count"] = state.get("step_count", 0) + 1
    if state["step_count"] >= state.get("max_steps", 200):
        # We enforce failure via integrator failure routing
        return Command(goto="integrator", update={"session_status": "failed"})

    tasks = state.get("tasks", [])
    
    # Are all tasks fully executed?
    if all(t.status in ("done", "failed") for t in tasks):
        logger.debug("All tasks completed. Routing to integrator.")
        return Command(goto="integrator")
        
    # Find next pending task mathematically matching dep specs
    next_task = None
    for t in tasks:
        if t.status == "pending":
            if not t.depends_on:
                next_task = t
                break
            # Dependency resolution
            deps_met = True
            for d in t.depends_on:
                if not any(dt.id == d and dt.status == "done" for dt in tasks):
                    deps_met = False
                    break
            if deps_met:
                next_task = t
                break
                
    if not next_task:
        logger.warning("No unblocked pending tasks remained. Halting graph to Integrator.")
        return Command(goto="integrator")
        
    # Mark in-progress
    next_task.status = "in_progress"
    update = {
        "tasks": tasks,
        "current_task_id": next_task.id
    }
    
    agent_type = next_task.agent_type
    logger.debug(f"Routing Task {next_task.id} -> {agent_type}_team")
    
    if agent_type == "refactor":
        goto = "refactor_team"
    elif agent_type == "test":
        goto = "test_team"
    elif agent_type == "doc":
        goto = "doc_team"
    elif agent_type == "review":
        goto = "review_agent"
    else:
        # Fallback
        goto = "refactor_team"

    return Command(goto=goto, update=update)
