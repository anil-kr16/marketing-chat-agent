"""
Consultation Registry - Central Registration for Consultation Components

This module provides centralized registration and discovery for all
consultation-related components, making it easy to extend and customize
the stateful consultation flow.

Key Features:
- Node registration and discovery for consultation graphs
- Question type and template management
- Evaluation strategy registration and selection
- Session storage backend registration

Architecture Benefits:
- Centralized component discovery and configuration
- Easy extension with new question types and evaluation strategies
- Plugin-like architecture for consultation components
- Clear separation of concerns between registration and implementation

Integration:
- Used by consultation graphs to discover available nodes
- Referenced by question prioritizer for available question types
- Utilized by completeness evaluator for evaluation strategies
- Applied by session manager for storage backend selection
"""

from typing import Dict, List, Callable, Any, Optional, Type
from dataclasses import dataclass
from enum import Enum

from src.utils.marketing_state import QuestionType, MarketingConsultantState
import logging

logger = logging.getLogger(__name__)


@dataclass
class NodeRegistration:
    """
    Registration information for a consultation node.
    
    This contains metadata about a node that can be used
    for dynamic discovery and configuration.
    """
    name: str
    description: str
    node_function: Callable
    input_type: Type
    output_type: Type
    tags: List[str]
    is_enabled: bool = True


@dataclass
class QuestionTemplate:
    """
    Template for generating questions of a specific type.
    
    This provides a structured way to define and manage
    question templates for different consultation scenarios.
    """
    question_type: QuestionType
    template: str
    context_variables: List[str]
    fallback_template: str
    priority: int = 5  # 1=highest, 10=lowest
    is_enabled: bool = True


@dataclass
class EvaluationStrategy:
    """
    Strategy for evaluating consultation completeness.
    
    This defines different approaches to determining when
    a consultation has gathered sufficient information.
    """
    name: str
    description: str
    evaluator_function: Callable
    min_questions: int
    quality_threshold: float
    is_enabled: bool = True


class ConsultationRegistry:
    """
    Central registry for all consultation components.
    
    This class manages registration and discovery of nodes, question templates,
    evaluation strategies, and other consultation components.
    
    Usage:
        registry = ConsultationRegistry()
        
        # Register a new node
        registry.register_node("custom_node", custom_node_function, ...)
        
        # Get available question templates
        templates = registry.get_question_templates(QuestionType.BUDGET)
        
        # Register evaluation strategy
        registry.register_evaluation_strategy("strict", strict_evaluator, ...)
    """
    
    def __init__(self):
        """Initialize the consultation registry with default components."""
        self.nodes: Dict[str, NodeRegistration] = {}
        self.question_templates: Dict[QuestionType, List[QuestionTemplate]] = {}
        self.evaluation_strategies: Dict[str, EvaluationStrategy] = {}
        self.session_backends: Dict[str, Type] = {}
        
        # Initialize with default components
        self._register_default_nodes()
        self._register_default_question_templates()
        self._register_default_evaluation_strategies()
        
        logger.info("Consultation registry initialized with default components")
    
    # === NODE REGISTRATION ===
    
    def register_node(
        self,
        name: str,
        node_function: Callable,
        description: str = "",
        input_type: Type = MarketingConsultantState,
        output_type: Type = MarketingConsultantState,
        tags: Optional[List[str]] = None,
        is_enabled: bool = True
    ) -> None:
        """
        Register a consultation node.
        
        Args:
            name: Unique name for the node
            node_function: Function implementing the node logic
            description: Human-readable description of node purpose
            input_type: Expected input type for the node
            output_type: Expected output type from the node
            tags: Optional tags for categorization and discovery
            is_enabled: Whether the node is currently enabled
        """
        if tags is None:
            tags = []
        
        registration = NodeRegistration(
            name=name,
            description=description,
            node_function=node_function,
            input_type=input_type,
            output_type=output_type,
            tags=tags,
            is_enabled=is_enabled
        )
        
        self.nodes[name] = registration
        logger.debug(f"Registered consultation node: {name}")
    
    def get_node(self, name: str) -> Optional[NodeRegistration]:
        """Get a registered node by name."""
        return self.nodes.get(name)
    
    def get_nodes_by_tag(self, tag: str) -> List[NodeRegistration]:
        """Get all nodes with a specific tag."""
        return [node for node in self.nodes.values() if tag in node.tags and node.is_enabled]
    
    def list_available_nodes(self) -> List[str]:
        """Get list of all available (enabled) node names."""
        return [name for name, node in self.nodes.items() if node.is_enabled]
    
    # === QUESTION TEMPLATE REGISTRATION ===
    
    def register_question_template(
        self,
        question_type: QuestionType,
        template: str,
        context_variables: Optional[List[str]] = None,
        fallback_template: Optional[str] = None,
        priority: int = 5,
        is_enabled: bool = True
    ) -> None:
        """
        Register a question template.
        
        Args:
            question_type: Type of question this template generates
            template: Template string with placeholder variables
            context_variables: List of variables that can be substituted
            fallback_template: Simpler template if context variables unavailable
            priority: Template priority (1=highest, 10=lowest)
            is_enabled: Whether the template is currently enabled
        """
        if context_variables is None:
            context_variables = []
        
        if fallback_template is None:
            fallback_template = template
        
        template_registration = QuestionTemplate(
            question_type=question_type,
            template=template,
            context_variables=context_variables,
            fallback_template=fallback_template,
            priority=priority,
            is_enabled=is_enabled
        )
        
        if question_type not in self.question_templates:
            self.question_templates[question_type] = []
        
        self.question_templates[question_type].append(template_registration)
        
        # Sort by priority (lower number = higher priority)
        self.question_templates[question_type].sort(key=lambda t: t.priority)
        
        logger.debug(f"Registered question template for {question_type.value}")
    
    def get_question_templates(self, question_type: QuestionType) -> List[QuestionTemplate]:
        """Get all templates for a specific question type, sorted by priority."""
        templates = self.question_templates.get(question_type, [])
        return [t for t in templates if t.is_enabled]
    
    def get_best_question_template(self, question_type: QuestionType) -> Optional[QuestionTemplate]:
        """Get the highest priority template for a question type."""
        templates = self.get_question_templates(question_type)
        return templates[0] if templates else None
    
    # === EVALUATION STRATEGY REGISTRATION ===
    
    def register_evaluation_strategy(
        self,
        name: str,
        evaluator_function: Callable,
        description: str = "",
        min_questions: int = 2,
        quality_threshold: float = 0.6,
        is_enabled: bool = True
    ) -> None:
        """
        Register an evaluation strategy.
        
        Args:
            name: Unique name for the strategy
            evaluator_function: Function that evaluates consultation completeness
            description: Human-readable description of the strategy
            min_questions: Minimum questions required before evaluation
            quality_threshold: Minimum quality score required
            is_enabled: Whether the strategy is currently enabled
        """
        strategy = EvaluationStrategy(
            name=name,
            description=description,
            evaluator_function=evaluator_function,
            min_questions=min_questions,
            quality_threshold=quality_threshold,
            is_enabled=is_enabled
        )
        
        self.evaluation_strategies[name] = strategy
        logger.debug(f"Registered evaluation strategy: {name}")
    
    def get_evaluation_strategy(self, name: str) -> Optional[EvaluationStrategy]:
        """Get an evaluation strategy by name."""
        strategy = self.evaluation_strategies.get(name)
        return strategy if strategy and strategy.is_enabled else None
    
    def list_available_strategies(self) -> List[str]:
        """Get list of all available (enabled) evaluation strategy names."""
        return [name for name, strategy in self.evaluation_strategies.items() if strategy.is_enabled]
    
    # === SESSION BACKEND REGISTRATION ===
    
    def register_session_backend(self, name: str, backend_class: Type) -> None:
        """Register a session storage backend."""
        self.session_backends[name] = backend_class
        logger.debug(f"Registered session backend: {name}")
    
    def get_session_backend(self, name: str) -> Optional[Type]:
        """Get a session backend class by name."""
        return self.session_backends.get(name)
    
    def list_session_backends(self) -> List[str]:
        """Get list of all available session backend names."""
        return list(self.session_backends.keys())
    
    # === PRIVATE INITIALIZATION METHODS ===
    
    def _register_default_nodes(self) -> None:
        """Register default consultation nodes."""
        # Import here to avoid circular imports
        from src.nodes.consultant.marketing_consultant_node import marketing_consultant_node
        from src.nodes.consultant.completeness_evaluator import evaluate_information_completeness
        from src.nodes.consultant.answer_processor import process_user_answer
        
        # Register core nodes
        self.register_node(
            "marketing_consultant",
            marketing_consultant_node,
            "Main consultation orchestration node",
            tags=["core", "orchestration"]
        )
        
        # Note: evaluate_information_completeness and process_user_answer are functions,
        # not nodes directly, so they don't get registered here
    
    def _register_default_question_templates(self) -> None:
        """Register default question templates for all question types."""
        
        # Product/Service templates
        self.register_question_template(
            QuestionType.PRODUCT_SERVICE,
            "What specifically would you like to promote or market?",
            [],
            "What are you promoting?",
            priority=1
        )
        
        self.register_question_template(
            QuestionType.PRODUCT_SERVICE,
            "Can you be more specific about {product}? What makes it special?",
            ["product"],
            "Can you tell me more about what you're promoting?",
            priority=2
        )
        
        # Target Audience templates
        self.register_question_template(
            QuestionType.TARGET_AUDIENCE,
            "Who is your target audience for {product}?",
            ["product"],
            "Who is your target audience?",
            priority=1
        )
        
        self.register_question_template(
            QuestionType.TARGET_AUDIENCE,
            "Can you describe your ideal customer? Consider age, profession, or interests.",
            [],
            "Who are your ideal customers?",
            priority=2
        )
        
        # Budget templates
        self.register_question_template(
            QuestionType.BUDGET,
            "What's your marketing budget range for this campaign?",
            [],
            "What's your budget?",
            priority=1
        )
        
        self.register_question_template(
            QuestionType.BUDGET,
            "Could you give me a rough budget range? For example: under $500, $500-$2000, or $2000+?",
            [],
            "What budget range are you thinking?",
            priority=2
        )
        
        # Channels templates
        self.register_question_template(
            QuestionType.CHANNELS,
            "Which marketing channels would you prefer to use?",
            [],
            "Which platforms should we use?",
            priority=1
        )
        
        self.register_question_template(
            QuestionType.CHANNELS,
            "Are you thinking social media (Instagram, Facebook), email marketing, or something else?",
            [],
            "What marketing channels do you prefer?",
            priority=2
        )
        
        # Tone/Style templates
        self.register_question_template(
            QuestionType.TONE_STYLE,
            "What tone or style should the marketing have?",
            [],
            "What tone should we use?",
            priority=1
        )
        
        self.register_question_template(
            QuestionType.TONE_STYLE,
            "Should the messaging be professional, casual and friendly, fun and energetic, or something else?",
            [],
            "Professional, casual, or fun tone?",
            priority=2
        )
        
        # Timeline templates
        self.register_question_template(
            QuestionType.TIMELINE,
            "When would you like to launch this campaign?",
            [],
            "When should this launch?",
            priority=1
        )
        
        # Goals/Metrics templates
        self.register_question_template(
            QuestionType.GOALS_METRICS,
            "What would success look like for this campaign?",
            [],
            "What are your goals?",
            priority=1
        )
        
        # Constraints templates
        self.register_question_template(
            QuestionType.CONSTRAINTS,
            "Are there any specific requirements or constraints I should know about?",
            [],
            "Any special requirements?",
            priority=1
        )
    
    def _register_default_evaluation_strategies(self) -> None:
        """Register default evaluation strategies."""
        
        # Import evaluation functions
        from src.nodes.consultant.completeness_evaluator import evaluate_information_completeness
        
        # Standard LLM-based evaluation
        self.register_evaluation_strategy(
            "llm_standard",
            evaluate_information_completeness,
            "Standard LLM-based completeness evaluation",
            min_questions=2,
            quality_threshold=0.6
        )
        
        # TODO: Add more evaluation strategies as they're implemented
        # self.register_evaluation_strategy(
        #     "heuristic_strict", 
        #     heuristic_strict_evaluator,
        #     "Strict heuristic-based evaluation",
        #     min_questions=4,
        #     quality_threshold=0.8
        # )


# === GLOBAL REGISTRY INSTANCE ===

# Create a global registry instance for use across the application
_global_registry: Optional[ConsultationRegistry] = None


def get_consultation_registry() -> ConsultationRegistry:
    """
    Get the global consultation registry instance.
    
    This provides a singleton pattern for component registration,
    ensuring consistency across the application.
    
    Returns:
        Global ConsultationRegistry instance
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = ConsultationRegistry()
        logger.info("Global consultation registry initialized")
    
    return _global_registry


def reset_consultation_registry() -> None:
    """
    Reset the global consultation registry.
    
    This is primarily used for testing and development.
    """
    global _global_registry
    _global_registry = None
