"""
Full Marketing Campaign Agent using LangGraph workflow.

This agent uses the complete marketing campaign graph for end-to-end campaign generation.
"""

from __future__ import annotations
from langsmith import traceable

from src.agents.core.base_agent import BaseAgent
from src.utils.state import MessagesState
from src.graphs.campaign.text_campaign_graph import get_full_marketing_graph


class FullMarketingAgent(BaseAgent):
    """
    Complete marketing campaign agent.
    
    Uses the full marketing campaign graph internally.
    Handles: Intent → Creative → Content → Review → Delivery
    """

    def __init__(self):
        """Initialize the agent with the full marketing graph."""
        super().__init__()
        self.graph = get_full_marketing_graph()

    @traceable(name="Full Marketing Agent")
    def run(self, state: MessagesState) -> MessagesState:
        """Run the complete marketing campaign workflow."""
        return self.graph.invoke(state)
