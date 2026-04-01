import os

from murmur.config import AppConfig


def test_config_basics():
    os.environ["MURMUR_MODEL"] = "ollama:llama3"
    config = AppConfig()
    assert config.model == "ollama:llama3"
    assert config.temperature == 0.2

    # Check default dictionary typing
    assert isinstance(config.mcp_servers, dict)
