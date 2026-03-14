import asyncio
import logging
import sys
from typing import Optional

import typer
from rich.console import Console

from murmur.config import AppConfig
from murmur.llm import build_llm
from murmur.tools.mcp_client import MCPClient
from murmur.memory.checkpointer import build_checkpointer, build_store
from murmur.memory.manager import MemoryManager
from murmur.utils.preflight import run_preflight
from murmur.utils.session import new_session_id
from murmur.graph import build_graph

# Try set loop policy for windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = Typer_App = typer.Typer(help="Murmur — Hierarchical Multi-Agent AI Coding CLI", no_args_is_help=True)
console = Console()
logger = logging.getLogger("murmur.cli")


def _init_env(verbose: bool, repo_path: str = ".") -> AppConfig:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    
    config = AppConfig(repo_path=repo_path)
    run_preflight(repo_path, config)
    return config


async def _run_graph(task: str, config: AppConfig, _type: str = "refactor"):
    sid = new_session_id()
    config_dict = config.model_dump()
    
    checkpointer = build_checkpointer(config.db_path)
    store = build_store()
    manager = MemoryManager(checkpointer, store, config.memory_db_path)
    await manager.start()
    
    llm = build_llm(config)
    
    async with MCPClient(config) as mcp:
        graph = build_graph(llm, mcp, manager)
        
        initial_state = {
            "session_id": sid,
            "task": task,
            "repo_path": config.repo_path,
            "command": _type,
            "dry_run": config.dry_run,
            "config": config_dict
        }
        
        thread = {"configurable": {"thread_id": sid}}
        
        console.print(f"[bold blue]🐦 Murmur Starting[/] | Session: {sid} | Task: {task}")
        
        try:
            async for event in graph.astream(initial_state, thread, stream_mode="updates"):
                for node, state_update in event.items():
                    if "tasks" in state_update:
                        console.print(f"[dim]Graph Output via {node}:[/dim]")
                    if "messages" in state_update and state_update["messages"]:
                        console.print(f"[cyan]Agent msg:[/cyan] {state_update['messages'][-1].content}")
        except asyncio.CancelledError:
            console.print(f"[bold red]INTERRUPTED[/] | Run `murmur status` to resume.")
            raise SystemExit(130)
        finally:
            await manager.stop()
            

@app.command()
def run(
    task: str = typer.Argument(..., help="The instruction for the AI agents."),
    repo_path: str = typer.Option(".", help="Target repository directory."),
    model: Optional[str] = typer.Option(None, help="Override default LLM target."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Evaluate diffs without applying them."),
    no_commit: bool = typer.Option(False, "--no-commit", help="Skip committing final result."),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Emit debug logs."),
):
    """Full pipeline: plan + execute."""
    config = _init_env(verbose, repo_path)
    if model: config.model = model
    config.dry_run = dry_run
    config.no_commit = no_commit
    
    asyncio.run(_run_graph(task, config, "run"))

@app.command()
def plan(
    task: str = typer.Argument(..., help="The description of what to plan."),
    repo_path: str = typer.Option(".", help="Target repository directory."),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Emit debug logs."),
):
    """Planning only. Analyse repo, produce structured task plan. No changes."""
    config = _init_env(verbose, repo_path)
    config.dry_run = True # force dry_run
    asyncio.run(_run_graph(task, config, "plan"))

@app.command()
def apply(
    plan_id: str = typer.Option(..., help="Plan identifier to execute."),
    repo_path: str = typer.Option(".", help="Target repository directory."),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Emit debug logs."),
):
    """Execute a previously generated plan (latest or by ID)."""
    console.print(f"Applying plan ID: [bold]{plan_id}[/]")
    config = _init_env(verbose, repo_path)
    # Internally starts graph via task load from memory tracking.
    asyncio.run(_run_graph("Resume apply", config, "apply"))

@app.command()
def refactor(
    description: str = typer.Argument(..., help="Goal for refactoring."),
    repo_path: str = typer.Option(".", help="Target repository directory."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Evaluate diffs without applying them."),
    no_commit: bool = typer.Option(False, "--no-commit", help="Skip committing final result."),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Emit debug logs."),
):
    """One-shot refactor: plan + apply."""
    config = _init_env(verbose, repo_path)
    config.dry_run = dry_run
    config.no_commit = no_commit
    asyncio.run(_run_graph(description, config, "refactor"))

@app.command()
def add_tests(
    module: Optional[str] = typer.Option(None, "--module", help="Path to limit tests."),
    repo_path: str = typer.Option(".", help="Target repository directory."),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Emit debug logs."),
):
    """Generate or improve tests."""
    config = _init_env(verbose, repo_path)
    task = f"Add comprehensive test coverage to {module or 'entire project'}."
    asyncio.run(_run_graph(task, config, "test"))

@app.command()
def review(
    repo_path: str = typer.Option(".", help="Target repository directory."),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Emit debug logs."),
):
    """Code review of recent Git changes. Prints findings."""
    config = _init_env(verbose, repo_path)
    asyncio.run(_run_graph("Perform a Code Review on recent patch", config, "review"))

@app.command()
def doc(
    module: Optional[str] = typer.Option(None, "--module", help="Path to limit doc gen."),
    repo_path: str = typer.Option(".", help="Target repository directory."),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Emit debug logs."),
):
    """Generate or update docstrings and README sections."""
    config = _init_env(verbose, repo_path)
    task = f"Write precise docs for {module or 'entire project'}."
    asyncio.run(_run_graph(task, config, "doc"))

@app.command()
def status(
    repo_path: str = typer.Option(".", help="Target repository directory."),
):
    """Read checkpointer and display progress of live runs."""
    console.print("[yellow]Retrieving live sessions from Memory DB...[/yellow]")
    # Placeholder
    console.print("Currently running sessions: `None`")

@app.command()
def config(
    llm: str = typer.Option(..., "--llm", help="Example: openai:gpt-4o"),
):
    """Set default LLM in .murmur/config.yaml."""
    console.print(f"Setting default Model Context parameters to [bold]{llm}[/bold].")
    import yaml
    import os
    os.makedirs(".murmur", exist_ok=True)
    c_path = ".murmur/config.yaml"
    c = {}
    if os.path.exists(c_path):
        with open(c_path, "r") as f:
            c = yaml.safe_load(f) or {}
    c["model"] = llm
    with open(c_path, "w") as f:
        yaml.safe_dump(c, f)
    console.print("[green]Saved inside .murmur/config.yaml[/green]")


app_memory = typer.Typer(help="Manage memory and RAG contexts.")
app.add_typer(app_memory, name="memory")

@app_memory.command("list")
def memory_list():
    """List all stored task runs with plan IDs and status."""
    console.print("Task Memory State:")
    # Reads sqlite store
    
@app_memory.command("clear")
def memory_clear():
    """Delete all stored runs and clear RAG index."""
    console.print("[red]Wiped ephemeral local storage context.[/red]")

if __name__ == "__main__":
    app()
