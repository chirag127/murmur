import asyncio
from typing import Optional, Dict, Any
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from murmur.state import OverallState

# Real implementation would poll task queue or listen to LangGraph stream_mode="updates".
class TerminalDisplay:
    """
    Renders the live terminal state using Rich.
    Updates via push.
    """
    def __init__(self, session_id: str, task: str):
        self.session_id = session_id[:8]
        self.task = task
        self.layout = Layout()
        self.run_data: Dict[str, Any] = {
            "tasks": [],
            "status_str": "initializing",
            "calls": []
        }
    
    def render_header(self) -> Panel:
        return Panel(
            f"TASK: {self.task}\nSTATUS: {self.run_data['status_str']}", 
            title=f"🐦 Murmur - {self.session_id}",
            border_style="blue"
        )
        
    def render_agents(self) -> Panel:
        table = Table(show_header=False, expand=True)
        for t in self.run_data["tasks"]:
            table.add_row(f"[{t.status}]{t.id}[/]", t.agent_type, t.title)
            
        return Panel(table, title="AGENTS & TASKS", border_style="cyan")
        
    def render_calls(self) -> Panel:
        table = Table(show_header=False, expand=True)
        for c in self.run_data["calls"][-10:]:
            table.add_row(c, style="dim")
        return Panel(table, title="TOOL CALLS", border_style="magenta")

    def make_layout(self) -> Layout:
        self.layout.split_column(
            Layout(name="header", size=4),
            Layout(name="main")
        )
        self.layout["main"].split_row(
            Layout(name="agents", ratio=1),
            Layout(name="calls", ratio=1)
        )
        self.layout["header"].update(self.render_header())
        self.layout["agents"].update(self.render_agents())
        self.layout["calls"].update(self.render_calls())
        return self.layout

    async def run(self, update_queue: asyncio.Queue) -> None:
        with Live(self.make_layout(), refresh_per_second=4, screen=False) as live:
            while True:
                data = await update_queue.get()
                if data.get("STOP"):
                    break
                self.run_data.update(data)
                live.update(self.make_layout())
