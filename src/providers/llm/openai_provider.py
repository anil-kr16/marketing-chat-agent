from __future__ import annotations

from typing import List

from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage

from src.config import get_config


class OpenAIProvider:
    """Thin wrapper to standardize LLM calls for OpenAI."""

    def __init__(self):
        cfg = get_config()
        self.client = ChatOpenAI(
            model=cfg.llm_model,
            temperature=cfg.temperature,
            api_key=cfg.openai_api_key,
        )

    def generate_chat(self, messages: List[BaseMessage]):
        return self.client.invoke(messages)

