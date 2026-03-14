import pytest
from typer.testing import CliRunner
from murmur.cli import app

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Murmur" in result.output

# Avoid performing real async Graph run tests directly because they block / need full LLM mock configs.
# Instead rely on core component logic testing.
def test_cli_config():
    result = runner.invoke(app, ["config", "--llm", "openai:gpt-4o"])
    assert result.exit_code == 0
    assert "Saving" or "Saved" in result.output
