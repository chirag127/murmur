import os
import subprocess
import asyncio
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("workspace_mcp", description="Built-in workspace server (files, git, tests)")


@mcp.tool()
def list_files(path: str = ".") -> List[str]:
    """List files in target directory."""
    result = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            result.append(os.path.relpath(os.path.join(root, f), path))
    return result


@mcp.tool()
def read_file(path: str) -> str:
    """Read full file content."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write exact content to a file. Overwrites entirely."""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing to {path}: {e}"


@mcp.tool()
def create_patch(path: str, patch: str) -> str:
    """Apply a unified diff patch to a file. (Placeholder execution)"""
    try:
        proc = subprocess.run(
            ["patch", "-p1", path],
            input=patch,
            text=True,
            capture_output=True,
        )
        if proc.returncode == 0:
            return "Patch applied successfully."
        else:
            return f"Patch failed:\n{proc.stderr}"
    except FileNotFoundError:
        return "Error: 'patch' command not available."


@mcp.tool()
def search_code(query: str, path: str = ".") -> List[Dict[str, Any]]:
    """Grep equivalent."""
    try:
        proc = subprocess.run(
            ["grep", "-rn", query, path],
            text=True,
            capture_output=True
        )
        lines = proc.stdout.splitlines()
        results = []
        for line in lines[:50]:  # limit to 50
            parts = line.split(":", 2)
            if len(parts) >= 3:
                results.append({"file": parts[0], "line": parts[1], "content": parts[2]})
        return results
    except FileNotFoundError:
        return [{"error": "grep not available on OS."}]


@mcp.tool()
def run_tests(test_path: str = ".") -> str:
    """Run pytest over the target path."""
    try:
        proc = subprocess.run(
            ["pytest", test_path, "-v"],
            text=True,
            capture_output=True
        )
        return proc.stdout or proc.stderr
    except FileNotFoundError:
        return "pytest not installed in environment."


@mcp.tool()
def git_status() -> str:
    """Show git status."""
    return subprocess.run(["git", "status", "-s"], text=True, capture_output=True).stdout


@mcp.tool()
def git_branch(branch_name: str) -> str:
    """Create and switch to a new branch, or just switch."""
    proc = subprocess.run(["git", "checkout", "-b", branch_name], text=True, capture_output=True)
    if proc.returncode != 0:
        return subprocess.run(["git", "checkout", branch_name], text=True, capture_output=True).stderr
    return f"Created branch {branch_name}"


@mcp.tool()
def git_commit(message: str) -> str:
    """Stage all changes and commit."""
    subprocess.run(["git", "add", "."], check=False)
    proc = subprocess.run(["git", "commit", "-m", message], text=True, capture_output=True)
    return proc.stdout or proc.stderr


@mcp.tool()
def git_diff(path: str = ".") -> str:
    """Show git diff."""
    return subprocess.run(["git", "diff", path], text=True, capture_output=True).stdout


if __name__ == "__main__":
    mcp.run()
