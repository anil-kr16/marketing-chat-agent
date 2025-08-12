"""
Marketing Consultant Node - Core Stateful Consultation Logic

This is the main orchestration node for the stateful marketing consultation flow.
It replaces the simple boolean detection with intelligent conversation management
that ensures high-quality campaigns through progressive information gathering.

Key Responsibilities:
1. Conversation Flow Control: Manages the consultation stages and transitions
2. Question Generation: Determines what to ask next based on context
3. Answer Processing: Extracts and validates user responses
4. Completeness Evaluation: Decides when we have enough info for campaigns
5. State Management: Updates consultation state safely and consistently

Architecture Philosophy:
- Beginner-friendly: Extensive comments explain the consultation logic
- Robust: Handles edge cases like unclear answers and conversation loops
- Extensible: Easy to add new question types or evaluation criteria
- Observable: Rich logging and state tracking for debugging

Integration Points:
- Uses LLM for intelligent question generation and evaluation
- Integrates with existing campaign creation when ready
- Provides fallback to simple chat for non-marketing queries
- Maintains session state across conversation turns
"""

import json
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from src.utils.marketing_state import (
    MarketingConsultantState, 
    ConsultationStage, 
    QuestionType
)
from src.config import get_config
import logging

# Initialize logger for detailed consultation tracking
logger = logging.getLogger(__name__)


@traceable(name="Marketing Consultant Node")
def marketing_consultant_node(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Main consultation orchestration node.
    
    This node manages the entire stateful consultation flow from initial
    unclear input ("market") to ready-for-campaign state with complete information.
    
    Flow Logic:
    1. INITIAL: Start consultation, ask first question
    2. GATHERING: Process answer, ask next question, or evaluate completeness
    3. VALIDATING: LLM evaluation of information adequacy  
    4. READY: All info gathered, prepare for campaign creation
    5. EXECUTING/COMPLETED: Hand off to campaign creation nodes
    
    Args:
        state: Current consultation state with conversation history
        
    Returns:
        Updated state with next question or completion status
        
    Example Flow:
        User: "market"
        Node: Ask "What would you like to market?"
        User: "coffee shop" 
        Node: Ask "Who's your target audience?"
        User: "local professionals"
        Node: Evaluate completeness → ask about budget
        User: "$2000"
        Node: Evaluate completeness → has_enough_info=True
    """
    logger.info(f"Starting consultation for session {state.session_id}")
    logger.debug(f"Current stage: {state.stage}, Questions asked: {state.question_count}")
    
    try:
        # === STAGE 1: INITIAL CONSULTATION START ===
        if state.stage == ConsultationStage.INITIAL:
            return _handle_initial_consultation(state)
        
        # === STAGE 2: GATHERING INFORMATION ===
        elif state.stage == ConsultationStage.GATHERING:
            return _handle_information_gathering(state)
        
        # === STAGE 3: VALIDATING COMPLETENESS ===
        elif state.stage == ConsultationStage.VALIDATING:
            return _handle_completeness_validation(state)
        
        # === STAGE 4: READY FOR CAMPAIGN ===
        elif state.stage == ConsultationStage.READY:
            return _handle_campaign_preparation(state)
        
        # === ERROR HANDLING ===
        else:
            logger.warning(f"Unknown consultation stage: {state.stage}")
            state.errors.append(f"Unknown stage: {state.stage}")
            state.stage = ConsultationStage.FAILED
            return state
            
    except Exception as e:
        logger.error(f"Error in consultation node: {str(e)}")
        state.errors.append(f"Consultation error: {str(e)}")
        state.stage = ConsultationStage.FAILED
        return state


def _handle_initial_consultation(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Handle the initial consultation start.
    
    This is where vague inputs like "market", "promote", or "launch billion dollar idea"
    get transformed into specific clarifying questions.
    
    Logic:
    1. Analyze initial input for any extractable information
    2. Generate first clarifying question based on what's missing
    3. Transition to GATHERING stage
    
    Args:
        state: Initial consultation state
        
    Returns:
        Updated state with first question asked
    """
    logger.info(f"Starting initial consultation for input: '{state.user_input}'")
    
    # Extract any initial information from the user's input
    _extract_initial_intent(state)
    
    # Generate the first clarifying question
    first_question = _generate_first_question(state)
    
    # Add the question to conversation history
    question_type = _determine_question_type(first_question)
    state.add_qa_pair(first_question, question_type)
    
    # Transition to gathering stage
    state.stage = ConsultationStage.GATHERING
    
    logger.info(f"Asked first question: {first_question}")
    return state


def _handle_information_gathering(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Handle the core information gathering phase.
    
    This is where we progressively build understanding through targeted questions.
    Each user response is processed and the next question is intelligently chosen.
    
    Logic:
    1. Process the user's latest answer
    2. Update parsed intent with new information  
    3. Decide next action: ask another question or validate completeness
    4. Generate next question if needed
    
    Args:
        state: State with user's latest response
        
    Returns:
        Updated state with next question or ready for validation
    """
    logger.info("Processing user response and determining next action")
    
    # Process the user's latest answer if available
    try:
        if hasattr(state, 'qa_history') and state.qa_history and state.qa_history[-1].get("answer"):
            _process_latest_answer(state)
    except Exception as e:
        logger.error(f"Error processing latest answer: {str(e)}")
        state.errors.append(f"Answer processing error: {str(e)}")
    
    # Check if we should stop questioning (max questions reached, etc.)
    if state.should_stop_questioning():
        logger.info("Reached questioning limit, moving to validation")
        state.stage = ConsultationStage.VALIDATING
        return state
    
    # Decide next action: ask another question or validate
    if _should_validate_completeness(state):
        logger.info("Sufficient information gathered, moving to validation")
        state.stage = ConsultationStage.VALIDATING
        return state
    
    # Generate and ask next question
    next_question = _generate_next_question(state)
    if next_question:
        question_type = _determine_question_type(next_question)
        state.add_qa_pair(next_question, question_type)
        logger.info(f"Asked next question: {next_question}")
    else:
        # No more questions to ask, move to validation
        logger.info("No more questions needed, moving to validation")
        state.stage = ConsultationStage.VALIDATING
    
    return state


def _handle_completeness_validation(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Handle the information completeness validation phase.
    
    This uses LLM intelligence to evaluate whether we have sufficient information
    to create a high-quality marketing campaign, replacing simple field checking.
    
    Logic:
    1. Use LLM to evaluate information completeness
    2. Identify any critical missing information
    3. Decide: ready for campaign, need more questions, or provide what we have
    
    Args:
        state: State with gathered information to evaluate
        
    Returns:
        Updated state with readiness decision
    """
    logger.info("Validating information completeness with LLM")
    
    # Use the improved completeness evaluator
    from src.nodes.consultant.completeness_evaluator import evaluate_information_completeness
    completeness_result = evaluate_information_completeness(state)
    
    if completeness_result["has_enough_info"]:
        # Ready to create campaign
        state.has_enough_info = True
        state.stage = ConsultationStage.READY
        state.missing_critical_info = []
        logger.info("LLM evaluation: Ready for campaign creation")
    
    elif state.question_count >= state.max_questions:
        # Reached question limit, proceed with what we have
        state.has_enough_info = True  # Force proceed
        state.stage = ConsultationStage.READY
        logger.info("Question limit reached, proceeding with available information")
    
    else:
        # Need more information, ask one more targeted question
        missing_info = completeness_result.get("missing_critical_info", [])
        state.missing_critical_info = missing_info
        
        if missing_info:
            next_question = _generate_targeted_question(state, missing_info[0])
            question_type = _determine_question_type(next_question)
            state.add_qa_pair(next_question, question_type)
            state.stage = ConsultationStage.GATHERING
            logger.info(f"Missing critical info, asked: {next_question}")
        else:
            # LLM says not enough but didn't specify what's missing
            state.has_enough_info = True
            state.stage = ConsultationStage.READY
            logger.info("LLM unclear on missing info, proceeding anyway")
    
    return state


def _handle_campaign_preparation(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Handle final campaign preparation.
    
    This stage prepares the gathered information for handoff to campaign creation
    nodes, ensuring all data is properly formatted and validated.
    
    Args:
        state: State ready for campaign creation
        
    Returns:
        Updated state prepared for campaign execution
    """
    logger.info("Preparing consultation results for campaign creation")
    
    # Generate final summary of gathered information
    state.final_plan = _generate_consultation_summary(state)
    
    # Ensure parsed_intent is complete and properly formatted
    _finalize_parsed_intent(state)
    
    # Mark as completed consultation
    state.stage = ConsultationStage.COMPLETED
    
    logger.info("Consultation completed, ready for campaign creation")
    return state


# === HELPER FUNCTIONS ===

def _extract_initial_intent(state: MarketingConsultantState) -> None:
    """
    Extract any obvious information from the initial user input.
    
    This handles cases where the user provides some context in their initial
    request, allowing us to skip obvious questions.
    
    Examples:
    - "promote coffee shop to millennials" → goal and audience partially known
    - "market fitness tracker on instagram facebook email for health enthusiasts" → goal, channels, and audience known
    - "launch" → nothing extractable, need everything
    """
    user_input = state.user_input.lower().strip()
    
    # Try to extract goal/product with improved patterns
    goal_patterns = [
        r'(?:promote|market|launch|advertise)\s+(.+?)(?:\s+to|\s+for|\s+on|\s+via|\s+using|$)',
        r'(?:campaign|ad|advertisement)\s+for\s+(.+?)(?:\s+to|\s+on|\s+via|\s+using|$)',
        r'(?:sell|selling)\s+(.+?)(?:\s+to|\s+for|\s+on|\s+via|\s+using|$)',
        r'(?:create|build)\s+(?:a\s+)?(?:marketing\s+)?(?:campaign\s+)?(?:for\s+)?(.+?)(?:\s+to|\s+for|\s+on|\s+via|\s+using|$)'
    ]
    
    for pattern in goal_patterns:
        match = re.search(pattern, user_input)
        if match:
            potential_goal = match.group(1).strip()
            # Avoid generic terms and clean up the goal
            if potential_goal not in ['it', 'this', 'that', 'something', 'business', 'idea']:
                # Remove common suffixes that might be captured
                potential_goal = re.sub(r'\s+(?:on|via|using|to|for|with).*$', '', potential_goal)
                
                # Check if the goal is too generic and needs clarification
                if potential_goal in ['one product', 'product', 'a product', 'my product']:
                    # Mark as needing clarification but don't set it
                    state.meta["needs_goal_clarification"] = True
                    logger.debug(f"Goal needs clarification: {potential_goal}")
                else:
                    state.parsed_intent["goal"] = potential_goal
                    logger.debug(f"Extracted goal from initial input: {potential_goal}")
                break
    
    # Try to extract audience with improved patterns
    audience_patterns = [
        r'(?:to|for)\s+(young\s+\w+|teenagers?|millennials?|professionals?|students?|seniors?|health\s+enthusiasts?|fitness\s+conscious|tech\s+savvy)',
        r'(?:to|for)\s+(\w+\s+(?:professionals?|students?|customers?|enthusiasts?|users?))',
        r'targeting\s+(.+?)(?:\s+on|\s+with|\s+via|\s+using|$)',
        r'for\s+(health\s+enthusiasts?|fitness\s+conscious|tech\s+savvy|young\s+professionals?)'
    ]
    
    for pattern in audience_patterns:
        match = re.search(pattern, user_input)
        if match:
            potential_audience = match.group(1).strip()
            state.parsed_intent["audience"] = potential_audience
            logger.debug(f"Extracted audience from initial input: {potential_audience}")
            break
    
    # Try to extract channels with improved patterns
    channel_patterns = [
        r'on\s+(.+?)(?:\s+for|\s+to|\s+with|\s+$)',
        r'via\s+(.+?)(?:\s+for|\s+to|\s+with|\s+$)',
        r'using\s+(.+?)(?:\s+for|\s+to|\s+with|\s+$)'
    ]
    
    for pattern in channel_patterns:
        match = re.search(pattern, user_input)
        if match:
            potential_channels = match.group(1).strip()
            # Extract channel names from the captured text
            channel_names = []
            channel_keywords = ['instagram', 'facebook', 'twitter', 'linkedin', 'email', 'social media', 'youtube', 'tiktok']
            
            for keyword in channel_keywords:
                if keyword in potential_channels.lower():
                    channel_names.append(keyword)
            
            if channel_names:
                state.parsed_intent["channels"] = ', '.join(channel_names)
                logger.debug(f"Extracted channels from initial input: {state.parsed_intent['channels']}")
                break
    
    # Try to extract budget hints
    budget_patterns = [
        r'(\d+\s*(?:dollars?|usd|euros?|pounds?|\$|€|£))',
        r'budget\s+(?:of\s+)?(\d+\s*(?:dollars?|usd|euros?|pounds?|\$|€|£))',
        r'(\d+[k])\s*(?:budget|dollars?|usd)',
        r'(\d+[m])\s*(?:budget|dollars?|usd)',
        r'with\s+(\$\d+)',  # "with $5000"
        r'(\$\d+)\s+budget',  # "$5000 budget"
        r'(\d+)\s+dollars?',  # "5000 dollars"
        r'(\d+)\s+usd'        # "5000 usd"
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, user_input)
        if match:
            potential_budget = match.group(1).strip()
            state.parsed_intent["budget"] = potential_budget
            logger.debug(f"Extracted budget from initial input: {potential_budget}")
            break
    
    # Try to extract timeline hints
    timeline_patterns = [
        r'for\s+(new\s*year|christmas|holiday|summer|winter|spring|fall|q[1-4]|quarter|month|week)',
        r'in\s+(new\s*year|christmas|holiday|summer|winter|spring|fall|q[1-4]|quarter|month|week)',
        r'(new\s*year|christmas|holiday|summer|winter|spring|fall|q[1-4]|quarter|month|week)',
        r'launch\s+(?:in|for)\s+(new\s*year|christmas|holiday|summer|winter|spring|fall|q[1-4]|quarter|month|week)'
    ]
    
    for pattern in timeline_patterns:
        match = re.search(pattern, user_input)
        if match:
            potential_timeline = match.group(1).strip()
            state.parsed_intent["timeline"] = potential_timeline
            logger.debug(f"Extracted timeline from initial input: {potential_timeline}")
            break
    
    # Try to extract tone/style hints
    tone_patterns = [
        r'(?:with\s+a\s+)?(professional|casual|fun|serious|energetic|calm|luxury|budget|friendly|formal)\s+(?:tone|style|approach)',
        r'(professional|casual|fun|serious|energetic|calm|luxury|budget|friendly|formal)\s+(?:marketing|campaign|approach)'
    ]
    
    for pattern in tone_patterns:
        match = re.search(pattern, user_input)
        if match:
            potential_tone = match.group(1).strip()
            state.parsed_intent["tone"] = potential_tone
            logger.debug(f"Extracted tone from initial input: {potential_tone}")
            break


def _generate_first_question(state: MarketingConsultantState) -> str:
    """
    Generate the first clarifying question based on what we know.
    
    This creates an appropriate opening question that acknowledges what
    we already understand and asks for the most critical missing piece.
    """
    # Build a summary of what we already know
    known_info = []
    if state.parsed_intent.get("goal"):
        known_info.append(f"goal: {state.parsed_intent['goal']}")
    if state.parsed_intent.get("audience"):
        known_info.append(f"audience: {state.parsed_intent['audience']}")
    if state.parsed_intent.get("channels"):
        known_info.append(f"channels: {state.parsed_intent['channels']}")
    if state.parsed_intent.get("budget"):
        known_info.append(f"budget: {state.parsed_intent['budget']}")
    if state.parsed_intent.get("tone"):
        known_info.append(f"tone: {state.parsed_intent['tone']}")
    
    # If we have no goal/product information, that's always first priority
    if not state.parsed_intent.get("goal"):
        # Check if we need goal clarification
        if state.meta.get("needs_goal_clarification"):
            return "I'd love to help you with marketing! I see you mentioned a product, but could you tell me specifically what product or service you'd like to promote?"
        else:
            return "I'd love to help you with marketing! What specifically would you like to promote or market?"
    
    # If we have goal but no audience, ask about target audience
    if not state.parsed_intent.get("audience"):
        goal = state.parsed_intent["goal"]
        if known_info:
            return f"Great! I can see you want to promote {goal}. Who is your target audience for this?"
        else:
            return f"Great! You want to promote {goal}. Who is your target audience for this?"
    
    # If we have goal and audience but no budget, ask about budget
    if not state.parsed_intent.get("budget"):
        return "Perfect! What's your marketing budget range for this campaign?"
    
    # If we have the basics, ask about channels
    if not state.parsed_intent.get("channels"):
        return "Excellent! Which marketing channels would you prefer to use - social media, email, local advertising, or others?"
    
    # If we have most information, ask about unique value proposition
    if len(known_info) >= 3:
        return "Great! You've provided most of the key details. What makes your offering unique or special compared to competitors?"
    
    # Fallback: ask about timeline
    return "When would you like to launch this campaign?"


def _generate_next_question(state: MarketingConsultantState) -> Optional[str]:
    """
    Generate the next question based on conversation history and missing information.
    
    This uses intelligent prioritization to ask the most important question next,
    considering what we've already asked and what's still needed.
    """
    # Determine what critical information is still missing
    missing_info = _identify_missing_critical_info(state)
    
    if not missing_info:
        return None  # No more questions needed
    
    # Prioritize questions based on importance
    question_priority = [
        "goal", "audience", "budget", "channels", "unique_value", "timeline"
    ]
    
    for priority in question_priority:
        if priority in missing_info:
            # Map priority string to correct QuestionType enum value
            question_type = _map_info_to_question_type(priority)
            if not state.has_asked_about(question_type):
                return _generate_question_for_type(priority, state)
    
    # If all priority questions asked, ask about any remaining missing info
    for info_type in missing_info:
        corresponding_question_type = _map_info_to_question_type(info_type)
        if not state.has_asked_about(corresponding_question_type):
            return _generate_question_for_type(info_type, state)
    
    return None  # All questions exhausted


def _generate_question_for_type(info_type: str, state: MarketingConsultantState) -> str:
    """Generate a specific question for a given information type."""
    goal = state.parsed_intent.get("goal", "your offering")
    
    question_templates = {
        "goal": "What specifically would you like to promote or market?",
        "audience": f"Who is your target audience for {goal}?",
        "budget": "What's your marketing budget range for this campaign?",
        "channels": "Which marketing channels would you prefer - social media, email, local advertising, or others?",
        "unique_value": f"What makes {goal} unique or special compared to competitors?",
        "timeline": "When would you like to launch this campaign?",
        "tone": "What tone or style should the marketing have - professional, casual, fun, or something else?"
    }
    
    return question_templates.get(info_type, f"Can you tell me more about the {info_type} for your campaign?")


def _generate_targeted_question(state: MarketingConsultantState, missing_info: str) -> str:
    """Generate a targeted question for specific missing information."""
    return _generate_question_for_type(missing_info, state)


def _process_latest_answer(state: MarketingConsultantState) -> None:
    """
    Process the user's latest answer and update parsed intent.
    
    This extracts relevant information from the user's response and updates
    the structured intent data accordingly.
    """
    try:
        if not hasattr(state, 'qa_history') or not state.qa_history:
            return
        
        latest_qa = state.qa_history[-1]
        answer = latest_qa.get("answer")
        question_type = latest_qa.get("question_type")
        
        if not answer:
            return
        
        # Update parsed intent based on question type and answer
        if question_type == QuestionType.PRODUCT_SERVICE.value:
            state.parsed_intent["goal"] = answer
        elif question_type == QuestionType.TARGET_AUDIENCE.value:
            state.parsed_intent["audience"] = answer
        elif question_type == QuestionType.BUDGET.value:
            state.parsed_intent["budget"] = answer
        elif question_type == QuestionType.CHANNELS.value:
            state.parsed_intent["channels"] = answer
        elif question_type == QuestionType.TONE_STYLE.value:
            state.parsed_intent["tone"] = answer
        elif question_type == QuestionType.TIMELINE.value:
            state.parsed_intent["timeline"] = answer
        elif question_type == QuestionType.GOALS_METRICS.value:
            state.parsed_intent["success_metrics"] = answer
        
        logger.debug(f"Updated parsed intent with {question_type}: {answer}")
    except Exception as e:
        logger.error(f"Error in _process_latest_answer: {str(e)}")


def _should_validate_completeness(state: MarketingConsultantState) -> bool:
    """
    Determine if we should move to completeness validation.
    
    This decides when we have enough information to warrant LLM evaluation
    rather than asking more questions.
    """
    # Always validate if we've asked many questions
    if state.question_count >= 4:
        return True
    
    # Validate if we have the core information
    core_fields = ["goal", "audience", "channels"]  # Budget is helpful but not critical
    has_core = all(state.parsed_intent.get(field) for field in core_fields)
    
    if has_core:
        return True
    
    # Don't validate too early
    if state.question_count < 2:
        return False
    
    return False


def _identify_missing_critical_info(state: MarketingConsultantState) -> List[str]:
    """Identify what critical information is still missing."""
    critical_fields = ["goal", "audience", "budget", "channels"]
    missing = []
    
    for field in critical_fields:
        if not state.parsed_intent.get(field):
            missing.append(field)
    
    return missing


def _determine_question_type(question: str) -> QuestionType:
    """Determine the type of question based on its content."""
    question_lower = question.lower()
    
    # Check for most specific patterns first (most specific to least specific)
    if any(word in question_lower for word in ["budget", "spend", "invest", "cost", "money", "dollars", "$"]):
        return QuestionType.BUDGET
    elif any(word in question_lower for word in ["audience", "target", "who", "customers", "demographics"]):
        return QuestionType.TARGET_AUDIENCE
    elif any(word in question_lower for word in ["channel", "platform", "where", "social", "email", "instagram", "facebook"]):
        return QuestionType.CHANNELS
    elif any(word in question_lower for word in ["tone", "style", "voice", "feel", "personality"]):
        return QuestionType.TONE_STYLE
    elif any(word in question_lower for word in ["when", "timeline", "launch", "date", "schedule"]):
        return QuestionType.TIMELINE
    elif any(word in question_lower for word in ["unique", "special", "different", "competitive", "advantage"]):
        return QuestionType.PRODUCT_SERVICE
    elif any(word in question_lower for word in ["what", "promote", "market", "product", "service"]):
        return QuestionType.PRODUCT_SERVICE
    else:
        return QuestionType.PRODUCT_SERVICE  # Default


def _map_info_to_question_type(info_type: str) -> QuestionType:
    """Map information type to question type enum."""
    mapping = {
        "goal": QuestionType.PRODUCT_SERVICE,
        "audience": QuestionType.TARGET_AUDIENCE,
        "budget": QuestionType.BUDGET,
        "channels": QuestionType.CHANNELS,
        "tone": QuestionType.TONE_STYLE,
        "timeline": QuestionType.TIMELINE,
        "unique_value": QuestionType.PRODUCT_SERVICE,
        "success_metrics": QuestionType.GOALS_METRICS
    }
    return mapping.get(info_type, QuestionType.PRODUCT_SERVICE)


def _evaluate_with_llm(state: MarketingConsultantState) -> Dict[str, Any]:
    """
    Use LLM to evaluate information completeness and quality.
    
    This replaces simple field checking with intelligent evaluation that
    considers context, quality, and campaign viability.
    """
    try:
        cfg = get_config()
        llm = ChatOpenAI(model=cfg.llm_model, temperature=0.1, api_key=cfg.openai_api_key)
        
        # Create evaluation prompt
        system_prompt = """
        You are a marketing consultant evaluating if we have enough information to create a high-quality marketing campaign.
        
        Consider:
        - Is the goal/product specific enough? (not just "business" or "idea")
        - Is the audience defined well enough to target? (not just "customers")
        - Is there budget information to guide strategy?
        - Are there channel preferences or constraints?
        
        Return ONLY a JSON object with:
        {
            "has_enough_info": boolean,
            "missing_critical_info": ["field1", "field2"],
            "reasoning": "brief explanation"
        }
        """
        
        # Prepare conversation context
        conversation_summary = state.get_conversation_summary()
        
        human_prompt = f"""
        Consultation Summary:
        {conversation_summary}
        
        Evaluate if this is sufficient for campaign creation.
        """
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        # Parse LLM response
        content = response.content.strip()
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                # Ultimate fallback
                result = {
                    "has_enough_info": state.question_count >= 3,
                    "missing_critical_info": [],
                    "reasoning": "LLM response parsing failed"
                }
        
        logger.debug(f"LLM evaluation result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"LLM evaluation failed: {str(e)}")
        # Fallback to simple heuristic
        missing = _identify_missing_critical_info(state)
        return {
            "has_enough_info": len(missing) <= 1,
            "missing_critical_info": missing,
            "reasoning": f"LLM evaluation failed: {str(e)}"
        }


def _generate_consultation_summary(state: MarketingConsultantState) -> str:
    """Generate a final summary for campaign creation."""
    summary_parts = [
        f"Marketing Consultation Summary:",
        f"Original Request: {state.user_input}",
        "",
        "Gathered Information:"
    ]
    
    for key, value in state.parsed_intent.items():
        if value:
            formatted_key = key.replace("_", " ").title()
            summary_parts.append(f"- {formatted_key}: {value}")
    
    if state.qa_history:
        summary_parts.append("")
        summary_parts.append("Key Discussion Points:")
        for i, qa in enumerate(state.qa_history, 1):
            if qa["answer"]:
                summary_parts.append(f"{i}. Q: {qa['question']}")
                summary_parts.append(f"   A: {qa['answer']}")
    
    return "\n".join(summary_parts)


def _finalize_parsed_intent(state: MarketingConsultantState) -> None:
    """Ensure parsed intent is properly formatted for campaign creation."""
    # Ensure required fields have some value
    if not state.parsed_intent.get("goal"):
        state.parsed_intent["goal"] = state.user_input
    
    if not state.parsed_intent.get("audience"):
        state.parsed_intent["audience"] = "general audience"
    
    if not state.parsed_intent.get("budget"):
        state.parsed_intent["budget"] = "not specified"
    
    if not state.parsed_intent.get("channels"):
        state.parsed_intent["channels"] = "recommended channels"
    
    # Convert to format expected by existing campaign nodes
    channels_str = state.parsed_intent.get("channels", "")
    if isinstance(channels_str, str):
        # Convert to list format expected by campaign nodes
        channels_list = [c.strip().title() for c in channels_str.replace(",", " ").split() if c.strip()]
        if not channels_list:
            channels_list = ["Email", "Instagram"]  # Default channels
        state.parsed_intent["channels"] = channels_list
