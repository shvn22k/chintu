"""OpenAI-compatible chat helpers (API keys from environment only)."""

from chintu.llm.client import chat_completion_json, chat_completion_text

__all__ = ["chat_completion_json", "chat_completion_text"]
