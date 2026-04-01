import os
import shutil
import subprocess

from rich.console import Console
from rich.panel import Panel

console = Console()


def run_preflight(repo_path: str, config) -> None:
    """Run mandatory environment precondition tests before graphs start."""
    errors = []
    warnings = []

    # 1. API Keys
    if not (
        config.model.startswith("ollama")
        or config.openai_api_key
        or config.anthropic_api_key
        or config.google_api_key
        or config.nvidia_api_key
        or config.groq_api_key
    ):
        errors.append("No LLM API key configured for remote models.")

    # 2. Node >= 18
    node_path = shutil.which("node")
    if not node_path:
        errors.append("'node' not found. It is required for MCP servers.")
    else:
        try:
            ver = subprocess.run(
                ["node", "-v"], capture_output=True, text=True
            ).stdout.strip()
            if int(ver.strip("v").split(".")[0]) < 18:
                errors.append(f"Node version {ver} is below required 18+")
        except Exception:
            errors.append("Failed to verify Node version.")

    # 3. NPX
    if not shutil.which("npx"):
        errors.append("'npx' is not found. Needed for docfork/sequential-thinking MCP.")

    # 4. UVX
    if not shutil.which("uvx"):
        errors.append("'uvx' is not found. Needed for kindly-web-search MCP.")

    # 5. Repo path config
    if not os.path.isdir(repo_path):
        errors.append(f"REPO_PATH '{repo_path}' is not a directory.")

    # 6. Git repo
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        errors.append(f"REPO_PATH '{repo_path}' is not a git repository.")

    # SOFT WARNINGS
    if not config.tavily_api_key:
        warnings.append("Tavily functionality missing (TAVILY_API_KEY).")
    if not config.exa_api_key:
        warnings.append("Exa functionality missing (EXA_API_KEY).")
    if not config.linkup_api_key:
        warnings.append("Linkup functionality missing (LINKUP_API_KEY).")
    if not config.ref_api_key:
        warnings.append("Ref.tools functionality missing (REF_API_KEY).")

    os.makedirs(".murmur", exist_ok=True)
    gi_path = os.path.join(repo_path, ".gitignore")
    if os.path.exists(gi_path):
        with open(gi_path, "r", encoding="utf-8") as f:
            if ".murmur" not in f.read():
                with open(gi_path, "a", encoding="utf-8") as fw:
                    fw.write("\n.murmur/\n")

    if errors:
        msg = "\n".join([f"[red]✗[/red] {e}" for e in errors])
        console.print(
            Panel(msg, title="[bold red]Murmur Preflight Failed", border_style="red")
        )
        raise SystemExit(1)

    if warnings:
        msg = "\n".join([f"[yellow]![/yellow] {w}" for w in warnings])
        console.print(
            Panel(
                msg,
                title="[bold yellow]Murmur Preflight Warnings",
                border_style="yellow",
            )
        )

    console.print(
        Panel(
            "[green]✓ All critical systems online.[/green]",
            title="[bold green]Murmur Preflight Passed",
            border_style="green",
        )
    )
