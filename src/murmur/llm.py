from typing import List
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import OpenAIEmbeddings

from murmur.config import AppConfig


def build_llm(config: AppConfig) -> BaseChatModel:
    """
    Build LLM using LangChain's init_chat_model based on provider:model format.
    Special handling for nvidia.
    """
    if config.model.startswith("nvidia:"):
        model_name = config.model.split(":", 1)[1]
        return ChatNVIDIA(
            model=model_name,
            api_key=config.nvidia_api_key or "not-used",
            base_url=config.nvidia_base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    # init_chat_model reads env vars automatically
    return init_chat_model(
        config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_embeddings(config: AppConfig) -> Embeddings:
    """Build embeddings for RAG system."""
    # Using OpenAI Embeddings as default; can be extended for local/other
    return OpenAIEmbeddings(
        model="text-embedding-3-small", 
        api_key=config.openai_api_key or "not-used"
    )


def list_models(config: AppConfig) -> List[str]:
    """Return known model IDs supporting tool calling."""
    return [
        "openai:gpt-4o",
        "anthropic:claude-3-5-sonnet-20240620",
        "google_genai:gemini-2.5-pro",
        "ollama:llama3",
        "nvidia:meta/llama-3.1-70b-instruct",
        "groq:llama-3.1-70b-versatile"
    ]
