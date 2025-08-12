"""
Question Prioritizer - Smart Question Sequencing for Marketing Consultation

This module handles intelligent question prioritization to ensure we gather
the most critical information first and avoid asking redundant questions.

Key Features:
- Priority-based question sequencing (critical → important → nice-to-have)
- Context-aware question generation based on previous answers
- Duplicate question prevention through conversation history analysis
- Adaptive questioning based on user response quality and detail

Architecture Benefits:
- Prevents overwhelming users with too many questions at once
- Ensures critical campaign information is gathered first
- Adapts to user conversation style (brief vs detailed responses)
- Provides fallback strategies for unclear or incomplete answers

Integration:
- Used by marketing_consultant_node to determine next questions
- Considers conversation history to avoid repetitive questioning
- Balances thoroughness with user experience efficiency
"""

from typing import List, Dict, Optional, Tuple
from enum import IntEnum

from src.utils.marketing_state import (
    MarketingConsultantState, 
    QuestionType,
    ConsultationStage
)
import logging

logger = logging.getLogger(__name__)


class QuestionPriority(IntEnum):
    """
    Priority levels for different types of marketing questions.
    
    Lower numbers = higher priority (asked first)
    This ensures we gather campaign-critical information before nice-to-have details.
    """
    CRITICAL = 1    # Essential for any campaign (goal, audience)
    IMPORTANT = 2   # Needed for effective campaigns (budget, channels)  
    USEFUL = 3      # Improves campaign quality (tone, timeline)
    OPTIONAL = 4    # Nice-to-have for optimization (metrics, constraints)


class QuestionPrioritizer:
    """
    Intelligent question prioritization and sequencing system.
    
    This class determines what questions to ask next based on:
    - Information criticality for campaign success
    - What we've already asked about
    - Quality and completeness of previous answers
    - User conversation patterns and responsiveness
    
    Example Usage:
        prioritizer = QuestionPrioritizer()
        next_question = prioritizer.get_next_question(state)
        if next_question:
            state.add_qa_pair(next_question["question"], next_question["type"])
    """
    
    def __init__(self):
        """Initialize the question prioritizer with predefined priorities and templates."""
        self._initialize_question_priorities()
        self._initialize_question_templates()
    
    def _initialize_question_priorities(self) -> None:
        """
        Define priority levels for different question types.
        
        This mapping ensures we ask the most critical questions first,
        regardless of user conversation style or response patterns.
        """
        self.question_priorities = {
            # === CRITICAL (Must have for any campaign) ===
            QuestionType.PRODUCT_SERVICE: QuestionPriority.CRITICAL,
            QuestionType.TARGET_AUDIENCE: QuestionPriority.CRITICAL,
            
            # === IMPORTANT (Needed for effective campaigns) ===
            QuestionType.BUDGET: QuestionPriority.IMPORTANT,
            QuestionType.CHANNELS: QuestionPriority.IMPORTANT,
            
            # === USEFUL (Improves campaign quality) ===
            QuestionType.TONE_STYLE: QuestionPriority.USEFUL,
            QuestionType.TIMELINE: QuestionPriority.USEFUL,
            
            # === OPTIONAL (Nice-to-have) ===
            QuestionType.GOALS_METRICS: QuestionPriority.OPTIONAL,
            QuestionType.CONSTRAINTS: QuestionPriority.OPTIONAL
        }
    
    def _initialize_question_templates(self) -> None:
        """
        Define question templates for different scenarios and contexts.
        
        These templates are context-aware and adapt based on what we
        already know about the user's campaign goals.
        """
        self.question_templates = {
            QuestionType.PRODUCT_SERVICE: {
                "initial": "I'd love to help you with marketing! What specifically would you like to promote or market?",
                "clarification": "Can you be more specific about what you're promoting? For example, is it a product, service, event, or business?",
                "details": "Tell me more about {product} - what makes it special or unique?"
            },
            
            QuestionType.TARGET_AUDIENCE: {
                "initial": "Who is your target audience for {product}?",
                "demographic": "Can you describe your ideal customer? Consider age, profession, interests, or lifestyle.",
                "psychographic": "What motivates your target audience? What problems does {product} solve for them?",
                "clarification": "When you say '{audience}', can you be more specific? For example, what age range or profession?"
            },
            
            QuestionType.BUDGET: {
                "initial": "What's your marketing budget range for this campaign?",
                "range": "Could you give me a rough budget range? For example: under $500, $500-$2000, $2000-$10000, or more?",
                "timeframe": "Is that budget for a one-time campaign or monthly marketing spend?",
                "constraints": "Are there any budget constraints or cost priorities I should know about?"
            },
            
            QuestionType.CHANNELS: {
                "initial": "Which marketing channels would you prefer to use?",
                "options": "Are you thinking social media (Instagram, Facebook), email marketing, local advertising, or a mix?",
                "audience_based": "Where does your target audience typically spend time online or discover new {product_type}?",
                "existing": "Do you already have established channels or social media accounts?"
            },
            
            QuestionType.TONE_STYLE: {
                "initial": "What tone or style should the marketing have?",
                "options": "Should the messaging be professional, casual and friendly, fun and energetic, or something else?",
                "brand_aligned": "How would you describe your brand personality in a few words?",
                "audience_matched": "What communication style would resonate best with {audience}?"
            },
            
            QuestionType.TIMELINE: {
                "initial": "When would you like to launch this campaign?",
                "urgency": "Is this time-sensitive or do we have flexibility with the launch date?",
                "duration": "How long should the campaign run - a few days, weeks, or ongoing?",
                "events": "Is this tied to any specific events, seasons, or product launches?"
            },
            
            QuestionType.GOALS_METRICS: {
                "initial": "What would success look like for this campaign?",
                "specific": "Are you primarily focused on brand awareness, sales, leads, or website traffic?",
                "measurable": "How will you measure if the campaign is working?",
                "realistic": "What would be a realistic goal given your budget and timeline?"
            },
            
            QuestionType.CONSTRAINTS: {
                "initial": "Are there any specific requirements or constraints I should know about?",
                "compliance": "Are there any industry regulations or compliance requirements?",
                "brand_guidelines": "Do you have existing brand guidelines or messaging requirements?",
                "limitations": "Are there any channels or approaches you definitely want to avoid?"
            }
        }
    
    def get_next_question(self, state: MarketingConsultantState) -> Optional[Dict[str, str]]:
        """
        Determine the next best question to ask based on current state.
        
        This is the main entry point for question prioritization. It considers:
        - What critical information is still missing
        - What we've already asked about
        - Quality of previous answers
        - Conversation flow and user response patterns
        
        Args:
            state: Current consultation state with conversation history
            
        Returns:
            Dict with "question", "type", and "context" or None if no more questions needed
            
        Example Return:
            {
                "question": "Who is your target audience for your coffee shop?",
                "type": "target_audience", 
                "context": "follow_up_critical"
            }
        """
        logger.debug(f"Determining next question for session {state.session_id}")
        
        # Get all missing question types, sorted by priority
        missing_types = self._get_missing_question_types(state)
        
        if not missing_types:
            logger.debug("No missing question types, consultation may be complete")
            return None
        
        # Select the highest priority missing question type
        next_type = missing_types[0]
        
        # Generate contextual question for this type
        question_info = self._generate_contextual_question(state, next_type)
        
        logger.info(f"Next question type: {next_type.value}, question: {question_info['question'][:50]}...")
        return question_info
    
    def _get_missing_question_types(self, state: MarketingConsultantState) -> List[QuestionType]:
        """
        Get question types we haven't asked about yet, sorted by priority.
        
        Args:
            state: Current consultation state
            
        Returns:
            List of QuestionType enums sorted by priority (highest first)
        """
        # Get all question types we haven't asked about
        all_types = list(QuestionType)
        missing_types = []
        
        for q_type in all_types:
            if not state.has_asked_about(q_type):
                # Check if we really need to ask this based on parsed intent
                if self._should_ask_about_type(state, q_type):
                    missing_types.append(q_type)
        
        # Sort by priority (critical first)
        missing_types.sort(key=lambda qt: self.question_priorities.get(qt, QuestionPriority.OPTIONAL))
        
        logger.debug(f"Missing question types: {[qt.value for qt in missing_types]}")
        return missing_types
    
    def _should_ask_about_type(self, state: MarketingConsultantState, question_type: QuestionType) -> bool:
        """
        Determine if we should ask about a specific question type.
        
        This considers whether we already have sufficient information
        from previous answers or initial input analysis.
        
        Args:
            state: Current consultation state
            question_type: The question type to evaluate
            
        Returns:
            True if we should ask about this type, False if we can skip it
        """
        # Map question types to parsed intent fields
        type_to_field = {
            QuestionType.PRODUCT_SERVICE: "goal",
            QuestionType.TARGET_AUDIENCE: "audience", 
            QuestionType.BUDGET: "budget",
            QuestionType.CHANNELS: "channels",
            QuestionType.TONE_STYLE: "tone",
            QuestionType.TIMELINE: "timeline",
            QuestionType.GOALS_METRICS: "success_metrics",
            QuestionType.CONSTRAINTS: "constraints"
        }
        
        field = type_to_field.get(question_type)
        if not field:
            return True  # Unknown type, ask to be safe
        
        # Check if we already have good information for this field
        current_value = state.parsed_intent.get(field)
        
        if not current_value:
            return True  # No information, definitely ask
        
        # For critical fields, ensure the information is substantial
        if question_type in [QuestionType.PRODUCT_SERVICE, QuestionType.TARGET_AUDIENCE]:
            return self._is_value_too_vague(current_value)
        
        # For other fields, any value is probably sufficient
        return False
    
    def _is_value_too_vague(self, value: str) -> bool:
        """
        Check if a parsed intent value is too vague and needs clarification.
        
        Args:
            value: The current value for an intent field
            
        Returns:
            True if the value needs more specificity
        """
        if not value or len(value.strip()) < 3:
            return True
        
        # Check for generic terms that need clarification
        vague_terms = [
            "business", "idea", "thing", "stuff", "product", "service",
            "customers", "people", "everyone", "users", "clients"
        ]
        
        value_lower = value.lower().strip()
        return value_lower in vague_terms
    
    def _generate_contextual_question(
        self, 
        state: MarketingConsultantState, 
        question_type: QuestionType
    ) -> Dict[str, str]:
        """
        Generate a contextual question for a specific question type.
        
        This creates questions that feel natural and build on previous
        conversation context rather than feeling scripted or robotic.
        
        Args:
            state: Current consultation state with conversation context
            question_type: The type of question to generate
            
        Returns:
            Dict with question text, type, and context information
        """
        # Get base templates for this question type
        templates = self.question_templates.get(question_type, {})
        
        # Determine the best template based on conversation context
        template_key = self._select_best_template(state, question_type, templates)
        template = templates.get(template_key, templates.get("initial", "Can you tell me more about this?"))
        
        # Fill in template placeholders with known information
        question = self._fill_template_placeholders(template, state)
        
        return {
            "question": question,
            "type": question_type.value,
            "context": template_key,
            "priority": self.question_priorities.get(question_type, QuestionPriority.OPTIONAL)
        }
    
    def _select_best_template(
        self, 
        state: MarketingConsultantState, 
        question_type: QuestionType,
        templates: Dict[str, str]
    ) -> str:
        """
        Select the most appropriate question template based on context.
        
        This considers conversation history, previous answer quality,
        and what information we already have.
        
        Args:
            state: Current consultation state
            question_type: Type of question we're generating
            templates: Available templates for this question type
            
        Returns:
            Key of the best template to use
        """
        # For first questions of each type, use initial template
        if not state.qa_history:
            return "initial"
        
        # Check if we need clarification on previous answers
        if self._needs_clarification(state, question_type):
            return "clarification"
        
        # For audience questions, adapt based on whether we know the product
        if question_type == QuestionType.TARGET_AUDIENCE:
            if state.parsed_intent.get("goal"):
                return "initial"  # We know the product, ask about audience
            else:
                return "demographic"  # General audience question
        
        # For budget questions, consider if we need ranges or specifics
        if question_type == QuestionType.BUDGET:
            if len(state.qa_history) <= 2:
                return "initial"
            else:
                return "range"  # User might need guidance on ranges
        
        # Default to initial template
        return "initial"
    
    def _needs_clarification(self, state: MarketingConsultantState, question_type: QuestionType) -> bool:
        """
        Check if previous answers related to this question type need clarification.
        
        Args:
            state: Current consultation state
            question_type: Question type to check
            
        Returns:
            True if clarification is needed
        """
        # Check if any previous answers were very brief or vague
        for qa in state.qa_history:
            if qa.get("question_type") == question_type.value and qa.get("answer"):
                answer = qa["answer"].strip()
                if len(answer) < 10 or self._is_value_too_vague(answer):
                    return True
        
        return False
    
    def _fill_template_placeholders(self, template: str, state: MarketingConsultantState) -> str:
        """
        Fill placeholder variables in question templates with known information.
        
        This makes questions feel more natural and conversational by
        incorporating information we've already learned.
        
        Args:
            template: Question template with placeholders like {product}
            state: Current consultation state with known information
            
        Returns:
            Question with placeholders filled in
        """
        # Extract known information for placeholder replacement
        replacements = {
            "product": state.parsed_intent.get("goal", "your offering"),
            "audience": state.parsed_intent.get("audience", "your target audience"),
            "product_type": self._extract_product_type(state.parsed_intent.get("goal", "")),
            "business": state.parsed_intent.get("goal", "your business")
        }
        
        # Handle special cases for product type
        goal = state.parsed_intent.get("goal", "").lower()
        if "app" in goal:
            replacements["product_type"] = "apps"
        elif "shop" in goal or "store" in goal:
            replacements["product_type"] = "stores"
        elif "service" in goal:
            replacements["product_type"] = "services"
        else:
            replacements["product_type"] = "products"
        
        # Replace placeholders in template
        try:
            question = template.format(**replacements)
        except KeyError as e:
            logger.warning(f"Template placeholder {e} not found, using template as-is")
            question = template
        
        return question
    
    def _extract_product_type(self, goal: str) -> str:
        """
        Extract a general product type from a specific goal description.
        
        Args:
            goal: Specific goal or product description
            
        Returns:
            General product type for use in templates
        """
        if not goal:
            return "products"
        
        goal_lower = goal.lower()
        
        # Check for specific types
        if any(word in goal_lower for word in ["app", "software", "platform", "tool"]):
            return "apps"
        elif any(word in goal_lower for word in ["shop", "store", "restaurant", "cafe"]):
            return "businesses"
        elif any(word in goal_lower for word in ["service", "consulting", "agency"]):
            return "services"
        elif any(word in goal_lower for word in ["event", "workshop", "course", "class"]):
            return "events"
        else:
            return "products"
    
    def evaluate_question_necessity(self, state: MarketingConsultantState) -> Dict[str, bool]:
        """
        Evaluate which question types are absolutely necessary vs optional.
        
        This helps determine when we have "enough" information to proceed
        with campaign creation vs when we need more critical details.
        
        Args:
            state: Current consultation state
            
        Returns:
            Dict mapping question types to necessity (True = must ask, False = optional)
        """
        necessity = {}
        
        for question_type in QuestionType:
            priority = self.question_priorities.get(question_type, QuestionPriority.OPTIONAL)
            already_asked = state.has_asked_about(question_type)
            has_info = self._should_ask_about_type(state, question_type)
            
            # Critical questions are necessary if not asked and info is missing
            if priority == QuestionPriority.CRITICAL:
                necessity[question_type.value] = not already_asked and has_info
            
            # Important questions are necessary if we have few questions asked
            elif priority == QuestionPriority.IMPORTANT:
                necessity[question_type.value] = (
                    not already_asked and 
                    has_info and 
                    state.question_count < 4
                )
            
            # Useful/Optional questions are not necessary but nice to have
            else:
                necessity[question_type.value] = False
        
        return necessity
    
    def get_question_progress_summary(self, state: MarketingConsultantState) -> Dict[str, any]:
        """
        Generate a summary of question progress for debugging and UX.
        
        Args:
            state: Current consultation state
            
        Returns:
            Dict with progress information and completion estimates
        """
        total_types = len(QuestionType)
        asked_types = len([qt for qt in QuestionType if state.has_asked_about(qt)])
        necessity = self.evaluate_question_necessity(state)
        necessary_remaining = sum(necessity.values())
        
        return {
            "total_question_types": total_types,
            "asked_question_types": asked_types,
            "completion_percentage": (asked_types / total_types) * 100,
            "necessary_questions_remaining": necessary_remaining,
            "can_proceed_to_campaign": necessary_remaining == 0,
            "recommendation": (
                "Ready for campaign creation" if necessary_remaining == 0
                else f"Need {necessary_remaining} more critical questions"
            )
        }
