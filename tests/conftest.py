import pytest
import os
import shutil
from unittest.mock import AsyncMock, patch

from murmur.config import AppConfig
from murmur.memory.checkpointer import build_checkpointer, build_store
from murmur.memory.manager import MemoryManager

@pytest.fixture
def mock_config(tmp_path):
    mc = AppConfig()
    mc.db_path = str(tmp_path / "murmur.db")
    mc.memory_db_path = str(tmp_path / "memory.db")
    mc.rag_db_path = str(tmp_path / "rag.db")
    mc.dry_run = True
    return mc

@pytest.fixture
async def mock_memory(mock_config):
    ckpt = build_checkpointer(mock_config.db_path)
    store = build_store()
    manager = MemoryManager(ckpt, store, mock_config.memory_db_path)
    await manager.start()
    yield manager
    await manager.stop()

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    # Provide a simple valid JSON string matching TaskSpec
    llm.ainvoke.return_value.content = '''```json
[
  {
    "id": "t1",
    "title": "dummy title",
    "description": "dummy desc",
    "target_paths": [],
    "agent_type": "refactor"
  }
]
```'''
    return llm
