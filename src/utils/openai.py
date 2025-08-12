"""
Helpers for constructing OpenAI clients and standard prompts.
"""

from __future__ import annotations

from typing import Tuple

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from src.config import get_config


def build_llm(model_override: str | None = None, temperature_override: float | None = None) -> ChatOpenAI:
    """Return a configured ChatOpenAI instance based on central config."""
    cfg = get_config()
    model = model_override or cfg.llm_model
    temperature = temperature_override if temperature_override is not None else cfg.temperature
    return ChatOpenAI(model=model, temperature=temperature, api_key=cfg.openai_api_key)


def simple_system_human(system: str, human: str) -> Tuple[SystemMessage, HumanMessage]:
    """Utility to build a common (system, human) message pair."""
    return SystemMessage(content=system), HumanMessage(content=human)

