from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any

from src.utils.state import MessagesState


class BaseAgent(ABC):
    """Abstract base class for agents.

    Agents accept and return a LangGraph-compatible state dict.
    """

    @abstractmethod
    def run(self, state: MessagesState) -> MessagesState:
        raise NotImplementedError

