import asyncio
import os
import pathspec
from typing import Dict, Any

from langchain_core.tools import tool


@tool
async def claim_file(path: str, agent_id: str, session_id: str) -> str:
    """Atomic file claim. Must be called before any write operation."""
    # This is a placeholder that ideally interacts with MemoryManager.
    # Injected at runtime rather than static to access global state.
    # It will be overridden by the agent context.
    return "ok"


@tool
async def release_file(path: str, agent_id: str, session_id: str) -> str:
    """Release a file claim."""
    return "released"


@tool
async def run_shell(command: str, timeout: int = 120) -> str:
    """Run an async shell command with a timeout."""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        ret = stdout.decode()
        if proc.returncode != 0:
            ret += f"\nError: {stderr.decode()}"
        return ret
    except asyncio.TimeoutError:
        return f"Timeout after {timeout} seconds."
    except Exception as e:
        return f"Execution error: {e}"


@tool
async def install_package(package: str, manager: str = "pip") -> str:
    """Install a package dependency."""
    cmd = f"{manager} install {package}"
    return await run_shell(cmd)


@tool
async def index_codebase(repo_path: str, max_files: int = 300) -> Dict[str, Any]:
    """Walk repo. Respects .gitignore. Return tree and hints."""
    ignore_path = os.path.join(repo_path, ".gitignore")
    lines = [".git/", ".murmur/", "__pycache__/"]
    if os.path.exists(ignore_path):
        with open(ignore_path, "r", encoding="utf-8") as f:
            lines.extend(f.readlines())
            
    spec = pathspec.PathSpec.from_lines("gitwildmatch", lines)
    
    tree = []
    count = 0
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, repo_path)
            if spec.match_file(rel):
                continue
                
            if count >= max_files:
                break
                
            tree.append(rel)
            count += 1
            
    return {"files": tree, "count": len(tree)}
