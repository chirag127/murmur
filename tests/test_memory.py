import pytest
import os
from murmur.memory.rag import RAGIndex

@pytest.mark.asyncio
async def test_memory_manager(mock_memory):
    # Claim test
    claimed = await mock_memory.claim_file("test.py", "agent_1", "sess_1")
    assert claimed is True
    
    # Conflict test
    claimed_again = await mock_memory.claim_file("test.py", "agent_2", "sess_1")
    assert claimed_again is False

    # Release test
    await mock_memory.release_file("test.py", "agent_1", "sess_1")
    claimed_third = await mock_memory.claim_file("test.py", "agent_2", "sess_1")
    assert claimed_third is True
    
@pytest.mark.asyncio
async def test_task_runs(mock_memory):
    data = {
        "plan_id": "abc",
        "session_id": "sess_123",
        "command": "refactor",
        "task": "do something",
        "status": "done",
        "created_at": "now",
        "completed_at": "later",
        "summary": "all good"
    }
    await mock_memory.save_task_run(data)
    runs = await mock_memory.list_task_runs()
    assert len(runs) == 1
    assert runs[0]["plan_id"] == "abc"

@pytest.mark.asyncio
async def test_rag_mock(tmp_path):
    rag = RAGIndex(str(tmp_path / "rag"), str(tmp_path))
    # It shouldn't crash on an empty repo
    await rag.build()
    res = await rag.query("test")
    assert isinstance(res, list)
