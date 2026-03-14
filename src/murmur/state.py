from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel
from langgraph.graph.message import add_messages


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class SessionStatus(str, Enum):
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class TaskSpec(BaseModel):
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    target_paths: List[str] = []
    assigned_to: Optional[str] = None
    depends_on: List[str] = []
    result_summary: Optional[str] = None
    git_branch: Optional[str] = None
    depth: int = 0
    agent_type: str = "refactor"  # "refactor"|"test"|"doc"|"review"


class DiffRecord(BaseModel):
    file_path: str
    agent_id: str
    action: str  # "created"|"modified"|"deleted"
    patch: str = ""
    before_hash: Optional[str] = None
    after_hash: Optional[str] = None
    timestamp: str = ""


class ErrorRecord(BaseModel):
    agent_id: str
    error_type: str
    message: str
    timestamp: str
    retries: int = 0


class OverallState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    session_id: str
    plan_id: str
    session_status: str
    command: str
    task: str
    repo_path: str
    dry_run: bool
    tasks: List[TaskSpec]
    current_task_id: Optional[str]
    file_locks: Dict[str, str]  # rel_path -> agent_id
    diff_log: List[DiffRecord]
    error_log: List[ErrorRecord]
    next_agent: str
    max_depth: int
    current_depth: int
    max_steps: int
    step_count: int
    error_count: int
    rag_context: Dict[str, str]
    memory_thread_id: str
    config: Dict[str, Any]
