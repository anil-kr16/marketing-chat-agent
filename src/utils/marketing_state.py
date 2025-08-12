"""
Marketing Consultant State Schema

This module defines the state schema for the stateful marketing consultation flow.
It replaces the simple boolean detection with a progressive information gathering
approach that ensures high-quality campaign creation.

Key Features:
- Progressive conversation tracking via qa_history
- Intelligent completeness evaluation with has_enough_info
- Stage-based flow control for better UX
- Session management for concurrent users
- Comprehensive intent parsing with validation

Architecture:
- Beginner-friendly: Each field has clear purpose and examples
- Extensible: Easy to add new fields or conversation types
- Type-safe: Full Pydantic validation with clear error messages
"""

from datetime import datetime
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field
from enum import Enum


class ConsultationStage(str, Enum):
    """
    Defines the different stages of marketing consultation flow.
    
    This enum helps track where we are in the conversation and
    what the next expected action should be.
    """
    INITIAL = "initial"              # Just started, need to understand request
    GATHERING = "gathering"          # Actively asking questions
    VALIDATING = "validating"        # Checking if we have enough info
    READY = "ready"                  # Ready to create campaign
    EXECUTING = "executing"          # Campaign creation in progress
    COMPLETED = "completed"          # Campaign created successfully
    FAILED = "failed"                # Something went wrong, need intervention


class QuestionType(str, Enum):
    """
    Categories of questions we ask during consultation.
    
    This helps prioritize what to ask next and ensures we cover
    all critical aspects of campaign planning.
    """
    PRODUCT_SERVICE = "product_service"    # What are you promoting?
    TARGET_AUDIENCE = "target_audience"    # Who is your audience?
    BUDGET = "budget"                      # What's your budget?
    CHANNELS = "channels"                  # Which platforms to use?
    TONE_STYLE = "tone_style"             # What tone/style?
    TIMELINE = "timeline"                  # When does this launch?
    GOALS_METRICS = "goals_metrics"        # What success looks like?
    CONSTRAINTS = "constraints"            # Any limitations or requirements?


class MarketingConsultantState(BaseModel):
    """
    Complete state for stateful marketing consultation flow.
    
    This replaces the simple boolean detection with a comprehensive
    conversation tracking system that ensures we gather all necessary
    information before creating campaigns.
    
    Benefits over previous approach:
    - No premature campaign execution for vague inputs like "market"
    - Progressive information gathering feels natural and consultative  
    - Quality control ensures campaigns have sufficient detail
    - Memory of conversation prevents repetitive questions
    
    Example usage:
        state = MarketingConsultantState(
            user_input="launch billion dollar idea",
            session_id="user123_20240812"
        )
        # Consultation flow will ask clarifying questions
        # Only proceed to campaign when has_enough_info=True
    """
    
    # === CORE INPUT & SESSION ===
    user_input: str = Field(
        description="The original user input that triggered consultation",
        example="launch billion dollar idea"
    )
    
    session_id: str = Field(
        default="",
        description="Unique session identifier for this consultation",
        example="user123_20240812_143022"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this consultation session started"
    )
    
    # === CONVERSATION TRACKING ===
    qa_history: List[Dict[str, Optional[str]]] = Field(
        default_factory=list,
        description="""
        Complete history of questions asked and answers received.
        
        Each entry has:
        - question: What we asked the user
        - answer: Their response (None if waiting for response)
        - question_type: Category of question (from QuestionType enum)
        - timestamp: When question was asked
        
        This prevents asking duplicate questions and builds context.
        """,
        example=[
            {
                "question": "What specifically would you like to market or promote?",
                "answer": "AI fitness app",
                "question_type": "product_service",
                "timestamp": "2024-08-12T14:30:22"
            },
            {
                "question": "Who is your target audience for this AI fitness app?",
                "answer": "Busy professionals aged 25-40",
                "question_type": "target_audience", 
                "timestamp": "2024-08-12T14:31:15"
            }
        ]
    )
    
    # === PARSED INFORMATION ===
    parsed_intent: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "goal": None,           # What they want to promote/achieve
            "audience": None,       # Target demographic/psychographic  
            "channels": None,       # Platforms to use (Instagram, email, etc.)
            "tone": None,          # Communication style (professional, fun, etc.)
            "budget": None,        # Available marketing spend
            "timeline": None,      # Launch date or campaign duration
            "unique_value": None,  # What makes this special/different
            "success_metrics": None # How to measure success
        },
        description="""
        Structured information extracted from conversation.
        
        This builds progressively as we ask questions and receive answers.
        Unlike the previous parse_intent_node that tried to extract everything
        at once, this builds context over multiple conversation turns.
        """
    )
    
    # === DECISION GATES ===
    has_enough_info: bool = Field(
        default=False,
        description="""
        Critical decision gate: Do we have sufficient information to create 
        a high-quality marketing campaign?
        
        This replaces the previous approach where campaigns were created
        immediately after intent parsing, even with incomplete information.
        
        Evaluation criteria:
        - Must have clear goal/product (not just "idea" or "business")
        - Must have specific audience (not just "customers")  
        - Must have realistic budget indication
        - Should have channel preferences
        
        Only when this is True do we proceed to campaign creation.
        """
    )
    
    stage: ConsultationStage = Field(
        default=ConsultationStage.INITIAL,
        description="Current stage of the consultation process"
    )
    
    # === QUALITY CONTROL ===
    missing_critical_info: List[str] = Field(
        default_factory=list,
        description="""
        List of critical information still needed before campaign creation.
        
        Examples: ["specific_product", "target_audience", "budget_range"]
        
        This helps prioritize what questions to ask next and provides
        transparency to the user about what information is still needed.
        """
    )
    
    question_count: int = Field(
        default=0,
        description="""
        Number of questions asked so far in this session.
        
        Used to prevent infinite questioning loops and know when to 
        suggest the user provide more details later or proceed with
        available information.
        
        Suggested limits:
        - 3-5 questions for simple campaigns
        - 6-8 questions for complex campaigns  
        - 8+ questions should trigger "let's proceed" or "more details later"
        """
    )
    
    max_questions: int = Field(
        default=8,
        description="Maximum questions before forcing a decision"
    )
    
    # === FINAL OUTPUT ===
    final_plan: Optional[str] = Field(
        default=None,
        description="""
        The final marketing plan/strategy generated after consultation.
        
        This is created only when has_enough_info=True and serves as the
        input to the actual campaign creation nodes.
        """
    )
    
    # === ERROR HANDLING ===
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors or issues encountered during consultation"
    )
    
    # === METADATA ===
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="""
        Metadata for debugging, analytics, and optimization.
        
        May include:
        - LLM model responses and costs
        - Response times for each question
        - User satisfaction indicators
        - A/B testing flags
        """
    )

    class Config:
        """Pydantic configuration for the state model."""
        # Allow extra fields for future extensibility
        extra = "allow"
        # Use enum values instead of names
        use_enum_values = True
        # Validate on assignment for immediate error detection
        validate_assignment = True
        # Allow arbitrary types for complex metadata
        arbitrary_types_allowed = True
        # Include example in schema for better documentation
        json_schema_extra = {
            "example": {
                "user_input": "promote my new coffee shop",
                "session_id": "user123_20240812",
                "qa_history": [
                    {
                        "question": "What makes your coffee shop unique?",
                        "answer": "We specialize in ethically sourced single-origin beans",
                        "question_type": "product_service"
                    }
                ],
                "parsed_intent": {
                    "goal": "promote coffee shop",
                    "audience": "coffee enthusiasts",
                    "channels": "instagram,local",
                    "tone": "friendly and authentic"
                },
                "has_enough_info": True,
                "stage": "ready"
            }
        }

    def add_qa_pair(
        self, 
        question: str, 
        question_type: QuestionType,
        answer: Optional[str] = None
    ) -> None:
        """
        Add a new question-answer pair to the conversation history.
        
        Args:
            question: The question being asked
            question_type: Category of question (helps with prioritization)
            answer: User's response (None if question just asked)
            
        This method ensures consistent formatting and automatic timestamping.
        """
        qa_entry = {
            "question": question,
            "answer": answer,
            "question_type": question_type.value,
            "timestamp": datetime.now().isoformat()
        }
        self.qa_history.append(qa_entry)
        self.question_count += 1

    def update_last_answer(self, answer: str) -> None:
        """
        Update the answer for the most recent question.
        
        Args:
            answer: User's response to the last question
            
        This is called when we receive a user response to our question.
        """
        if self.qa_history:
            self.qa_history[-1]["answer"] = answer

    def get_unanswered_questions(self) -> List[Dict]:
        """
        Get questions that are still waiting for answers.
        
        Returns:
            List of question entries where answer is None
            
        Useful for determining if we're waiting for user input.
        """
        return [qa for qa in self.qa_history if qa["answer"] is None]

    def get_answered_questions_by_type(self, question_type: QuestionType) -> List[Dict]:
        """
        Get all answered questions of a specific type.
        
        Args:
            question_type: The type of questions to retrieve
            
        Returns:
            List of answered questions of the specified type
            
        Useful for checking if we've already covered a topic.
        """
        return [
            qa for qa in self.qa_history 
            if qa["question_type"] == question_type.value and qa["answer"] is not None
        ]

    def has_asked_about(self, question_type: QuestionType) -> bool:
        """
        Check if we've already asked about a specific topic.
        
        Args:
            question_type: The type of question to check
            
        Returns:
            True if we've asked about this topic, False otherwise
            
        Prevents asking duplicate questions.
        """
        return any(
            qa["question_type"] == question_type.value 
            for qa in self.qa_history
        )

    def is_waiting_for_answer(self) -> bool:
        """
        Check if we're currently waiting for a user response.
        
        Returns:
            True if the last question hasn't been answered yet
            
        Used to determine conversation flow state.
        """
        return bool(self.get_unanswered_questions())

    def should_stop_questioning(self) -> bool:
        """
        Determine if we should stop asking questions and proceed.
        
        Returns:
            True if we've asked enough questions or have sufficient info
            
        Prevents infinite questioning loops.
        """
        return (
            self.question_count >= self.max_questions or
            self.has_enough_info or
            len(self.missing_critical_info) == 0
        )

    def get_conversation_summary(self) -> str:
        """
        Generate a human-readable summary of the consultation so far.
        
        Returns:
            Formatted summary of questions asked and information gathered
            
        Useful for debugging and user transparency.
        """
        summary_lines = [f"Consultation Summary for: {self.user_input}"]
        summary_lines.append(f"Stage: {self.stage}")
        summary_lines.append(f"Questions asked: {self.question_count}")
        summary_lines.append(f"Has enough info: {self.has_enough_info}")
        
        if self.qa_history:
            summary_lines.append("\nConversation:")
            for i, qa in enumerate(self.qa_history, 1):
                summary_lines.append(f"  Q{i}: {qa['question']}")
                if qa['answer']:
                    summary_lines.append(f"  A{i}: {qa['answer']}")
                else:
                    summary_lines.append(f"  A{i}: [Waiting for response]")
        
        if self.parsed_intent:
            summary_lines.append("\nGathered Information:")
            for key, value in self.parsed_intent.items():
                if value:
                    summary_lines.append(f"  {key}: {value}")
        
        return "\n".join(summary_lines)
