"""
Consultant Nodes Package

This package contains all nodes related to the stateful marketing consultation flow.
These nodes replace the simple boolean detection with intelligent conversation management.

Key Components:
- marketing_consultant_node: Main consultation orchestration logic
- question_prioritizer: Smart question sequencing and prioritization  
- completeness_evaluator: LLM-driven assessment of information adequacy
- answer_processor: Extract and validate user responses

Architecture Benefits:
- Stateful conversation tracking prevents repetitive questions
- Progressive information gathering ensures campaign quality
- Intelligent routing based on conversation context
- Fallback strategies for edge cases and user confusion
"""

from .marketing_consultant_node import marketing_consultant_node
from .question_prioritizer import QuestionPrioritizer
from .completeness_evaluator import evaluate_information_completeness
from .answer_processor import process_user_answer

__all__ = [
    "marketing_consultant_node",
    "QuestionPrioritizer", 
    "evaluate_information_completeness",
    "process_user_answer"
]
