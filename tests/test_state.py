import pytest
from murmur.state import TaskSpec, TaskStatus

def test_state_taskspec():
    task = TaskSpec(id="123", title="foo", description="bar")
    assert task.status == TaskStatus.PENDING
    assert task.agent_type == "refactor"
    assert task.depends_on == []
    
    # Modify state
    task.status = TaskStatus.IN_PROGRESS
    assert task.status == "in_progress"
