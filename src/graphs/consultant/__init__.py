"""
Consultant Graphs Package

This package contains graph definitions for the stateful marketing consultation flow.
These graphs orchestrate the intelligent conversation management that replaces
simple boolean detection with progressive information gathering.

Key Components:
- stateful_marketing_graph: Main consultation flow orchestration
- session_management_graph: Session lifecycle and cleanup management
- integration_bridges: Connections to existing campaign creation graphs

Architecture Benefits:
- Clear separation of consultation vs campaign creation logic
- Stateful conversation tracking with memory persistence
- Intelligent routing based on conversation context and readiness
- Graceful fallback strategies for edge cases and errors

Integration Points:
- Connects to existing campaign graphs when consultation is complete
- Provides session management for concurrent user consultations
- Bridges stateful consultation state to campaign execution state
"""

from .stateful_marketing_graph import create_stateful_marketing_graph

__all__ = [
    "create_stateful_marketing_graph"
]
