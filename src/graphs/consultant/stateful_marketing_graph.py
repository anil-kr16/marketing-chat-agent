"""
Stateful Marketing Graph - LangGraph Orchestration for Intelligent Consultation

This module defines the LangGraph flow that orchestrates the stateful marketing
consultation process. It replaces simple boolean detection with intelligent
conversation management that ensures high-quality campaign creation.

Key Features:
- Stateful conversation tracking through multiple interaction turns
- Intelligent question prioritization and sequencing
- LLM-driven completeness evaluation and quality assessment
- Graceful handling of edge cases and user conversation patterns
- Seamless integration with existing campaign creation workflows

Graph Flow:
1. ENTRY → Initial consultation setup and first question
2. GATHERING → Iterative question-answer cycles with quality assessment
3. VALIDATION → LLM evaluation of information completeness
4. READY → Preparation for campaign creation handoff
5. INTEGRATION → Bridge to existing campaign execution graphs

Architecture Benefits:
- Beginner-friendly: Extensive comments explain each node and edge
- Robust: Handles conversation loops, unclear responses, and edge cases
- Observable: Rich state tracking and logging for debugging
- Extensible: Easy to add new question types or evaluation criteria

Integration Strategy:
- Maintains compatibility with existing MessagesState format
- Provides conversion utilities between consultation and campaign states
- Preserves session information for multi-turn conversations
"""

from typing import Dict, Any, List, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END

from src.utils.marketing_state import (
    MarketingConsultantState, 
    ConsultationStage,
    QuestionType
)
from src.utils.state import MessagesState
from src.nodes.consultant.marketing_consultant_node import marketing_consultant_node
from src.nodes.consultant.question_prioritizer import QuestionPrioritizer
from src.nodes.consultant.completeness_evaluator import evaluate_information_completeness
from src.nodes.consultant.answer_processor import process_user_answer
import logging

logger = logging.getLogger(__name__)


def create_stateful_marketing_graph() -> StateGraph:
    """
    Create the main stateful marketing consultation graph.
    
    This graph orchestrates the intelligent conversation flow that gathers
    sufficient information for high-quality campaign creation.
    
    Graph Structure:
    
    START → consultation_entry → questioning_loop ↔ answer_processing
                ↓                      ↓
        completeness_validation → campaign_ready → CAMPAIGN_HANDOFF
                ↓                      ↓
        error_handling → END    conversation_complete → END
    
    Key Decision Points:
    - Should we ask another question or validate completeness?
    - Is the gathered information sufficient for campaign creation?
    - Should we handle errors gracefully or escalate?
    
    Returns:
        Configured StateGraph ready for compilation and execution
        
    Example Usage:
        graph = create_stateful_marketing_graph()
        compiled_graph = graph.compile()
        
        initial_state = MarketingConsultantState(
            user_input="market my coffee shop",
            session_id="user123_session"
        )
        
        result = compiled_graph.invoke(initial_state)
        # Result contains complete consultation with campaign-ready information
    """
    logger.info("Creating stateful marketing consultation graph")
    
    # Initialize the graph with our custom state
    graph = StateGraph(MarketingConsultantState)
    
    # === CORE CONSULTATION NODES ===
    
    # Entry point: Initialize consultation and ask first question
    graph.add_node("consultation_entry", consultation_entry_node)
    
    # Main consultation orchestrator
    graph.add_node("consultation_orchestrator", marketing_consultant_node)
    
    # Answer processing and intent updating
    graph.add_node("answer_processor", answer_processing_node)
    
    # Completeness evaluation using LLM intelligence
    graph.add_node("completeness_evaluator", completeness_evaluation_node)
    
    # Campaign preparation and handoff
    graph.add_node("campaign_preparation", campaign_preparation_node)
    
    # Error handling and recovery
    graph.add_node("error_handler", error_handling_node)
    
    # === GRAPH FLOW DEFINITION ===
    
    # Start at consultation entry
    graph.set_entry_point("consultation_entry")
    
    # Entry → Main consultation flow
    graph.add_edge("consultation_entry", "consultation_orchestrator")
    
    # Main consultation orchestrator routes based on stage
    graph.add_conditional_edges(
        "consultation_orchestrator",
        _route_from_consultation,
        {
            "continue_gathering": "answer_processor",
            "validate_completeness": "completeness_evaluator", 
            "prepare_campaign": "campaign_preparation",
            "handle_error": "error_handler",
            "end_consultation": END
        }
    )
    
    # Answer processor routes based on quality and next action
    graph.add_conditional_edges(
        "answer_processor",
        _route_from_answer_processing,
        {
            "back_to_consultation": "consultation_orchestrator",
            "validate_completeness": "completeness_evaluator",
            "handle_error": "error_handler"
        }
    )
    
    # Completeness evaluator decides readiness
    graph.add_conditional_edges(
        "completeness_evaluator", 
        _route_from_completeness_evaluation,
        {
            "ask_more_questions": "consultation_orchestrator",
            "ready_for_campaign": "campaign_preparation",
            "handle_error": "error_handler"
        }
    )
    
    # Campaign preparation leads to end (handoff to campaign graphs)
    graph.add_edge("campaign_preparation", END)
    
    # Error handler can recover or end
    graph.add_conditional_edges(
        "error_handler",
        _route_from_error_handling,
        {
            "retry_consultation": "consultation_orchestrator",
            "end_with_error": END
        }
    )
    
    logger.info("Stateful marketing consultation graph created successfully")
    return graph


# === NODE IMPLEMENTATIONS ===

def consultation_entry_node(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Entry point for stateful marketing consultation.
    
    This node initializes the consultation session and sets up the first
    interaction. It handles both fresh consultations and session resumption.
    
    Responsibilities:
    - Session ID generation and validation
    - Initial state setup and validation
    - First question generation based on user input analysis
    - Conversation history initialization
    
    Args:
        state: Initial consultation state (may be minimal)
        
    Returns:
        State with session initialized and first question ready
    """
    logger.info(f"Starting consultation entry for: '{state.user_input}'")
    
    try:
        # Ensure session ID exists
        if not state.session_id:
            state.session_id = f"consultation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize stage if not set
        if state.stage == ConsultationStage.INITIAL or not state.stage:
            state.stage = ConsultationStage.INITIAL
        
        # Clear any existing errors
        state.errors = []
        
        # Ensure question_count is initialized
        if not hasattr(state, 'question_count') or state.question_count is None:
            state.question_count = 0
        
        # Set timestamp if not already set
        if not state.timestamp:
            state.timestamp = datetime.now()
        
        logger.info(f"Consultation session initialized: {state.session_id}")
        return state
        
    except Exception as e:
        logger.error(f"Error in consultation entry: {str(e)}")
        state.errors.append(f"Consultation entry error: {str(e)}")
        state.stage = ConsultationStage.FAILED
        return state


def answer_processing_node(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Process user answers and update consultation state.
    
    This node handles the processing of user responses, extracting relevant
    information and updating the consultation state accordingly.
    
    Key Features:
    - Natural language processing of user responses
    - Information extraction and intent updating
    - Quality assessment and feedback generation
    - Conversation flow control based on response analysis
    
    Args:
        state: Consultation state with user's latest response
        
    Returns:
        State updated with processed information and next action plan
    """
    logger.debug("Processing user answer and updating consultation state")
    
    try:
        # Check if we're waiting for a user response
        if state.is_waiting_for_answer():
            # Get the latest user input (this would come from the conversation interface)
            # For now, we'll assume the latest response is in the last QA entry
            last_qa = state.qa_history[-1] if state.qa_history else None
            
            if last_qa and last_qa.get("answer"):
                # Process the user's response
                processing_result = process_user_answer(state, last_qa["answer"])
                
                # Update parsed intent with extracted information
                if processing_result.get("updated_intent"):
                    state.parsed_intent.update(processing_result["updated_intent"])
                
                # Store processing metadata for debugging
                state.meta["last_answer_processing"] = processing_result
                
                logger.info(f"Processed answer, extracted: {list(processing_result.get('extracted_info', {}).keys())}")
            
        return state
        
    except Exception as e:
        logger.error(f"Error in answer processing: {str(e)}")
        state.errors.append(f"Answer processing error: {str(e)}")
        return state


def completeness_evaluation_node(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Evaluate information completeness using LLM intelligence.
    
    This node determines whether we have sufficient information to create
    a high-quality marketing campaign, using sophisticated evaluation criteria.
    
    Key Features:
    - LLM-driven completeness assessment
    - Quality evaluation beyond simple field checking
    - Specific recommendations for missing information
    - Confidence scoring for transparency
    
    Args:
        state: Consultation state with gathered information
        
    Returns:
        State with completeness evaluation and recommendations
    """
    logger.info("Evaluating information completeness for campaign readiness")
    
    try:
        # Perform comprehensive completeness evaluation
        evaluation_result = evaluate_information_completeness(state)
        
        # Update state with evaluation results
        state.has_enough_info = evaluation_result.get("has_enough_info", False)
        state.missing_critical_info = evaluation_result.get("missing_critical_info", [])
        
        # Store evaluation metadata
        state.meta["completeness_evaluation"] = evaluation_result
        
        # Transition stage based on evaluation
        if state.has_enough_info:
            state.stage = ConsultationStage.READY
            logger.info("Evaluation complete: Ready for campaign creation")
        else:
            state.stage = ConsultationStage.GATHERING
            logger.info(f"Evaluation complete: Need more info - {state.missing_critical_info}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in completeness evaluation: {str(e)}")
        state.errors.append(f"Completeness evaluation error: {str(e)}")
        state.stage = ConsultationStage.FAILED
        return state


def campaign_preparation_node(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Prepare consultation results for campaign creation handoff.
    
    This node finalizes the consultation process and prepares the gathered
    information for integration with existing campaign creation workflows.
    
    Key Features:
    - Information formatting for campaign graph compatibility
    - Final validation and cleanup of gathered data
    - Consultation summary generation
    - Session completion and cleanup preparation
    
    Args:
        state: Consultation state ready for campaign creation
        
    Returns:
        State prepared for handoff to campaign creation systems
    """
    logger.info("Preparing consultation results for campaign creation")
    
    try:
        # Finalize parsed intent formatting
        _finalize_intent_formatting(state)
        
        # Generate consultation summary
        state.final_plan = _generate_final_consultation_summary(state)
        
        # Set completion stage and timestamp
        state.stage = ConsultationStage.COMPLETED
        state.meta["completion_timestamp"] = datetime.now().isoformat()
        
        # Calculate consultation metrics for analytics
        state.meta["consultation_metrics"] = _calculate_consultation_metrics(state)
        
        logger.info(f"Campaign preparation complete for session: {state.session_id}")
        return state
        
    except Exception as e:
        logger.error(f"Error in campaign preparation: {str(e)}")
        state.errors.append(f"Campaign preparation error: {str(e)}")
        state.stage = ConsultationStage.FAILED
        return state


def error_handling_node(state: MarketingConsultantState) -> MarketingConsultantState:
    """
    Handle errors and attempt recovery when possible.
    
    This node provides graceful error handling and recovery strategies
    for various failure modes in the consultation process.
    
    Recovery Strategies:
    - Temporary LLM failures → Retry with fallback evaluation
    - State corruption → Reset to last known good state
    - User confusion → Provide helpful guidance and restart
    - System errors → Graceful degradation with user notification
    
    Args:
        state: Consultation state with error information
        
    Returns:
        State with error resolution and recovery plan
    """
    logger.warning(f"Handling consultation errors: {state.errors}")
    
    try:
        # Analyze error types and determine recovery strategy
        error_analysis = _analyze_consultation_errors(state)
        
        if error_analysis["can_recover"]:
            # Attempt recovery
            recovery_action = error_analysis["recovery_action"]
            
            if recovery_action == "reset_to_gathering":
                state.stage = ConsultationStage.GATHERING
                state.errors = []  # Clear errors after recovery
                logger.info("Recovered by resetting to gathering stage")
            
            elif recovery_action == "retry_last_action":
                # Keep current stage but clear errors for retry
                state.errors = []
                logger.info("Recovered by retrying last action")
            
            elif recovery_action == "provide_guidance":
                # Add helpful message and continue
                if not state.qa_history:
                    # Add guidance question
                    state.add_qa_pair(
                        "I'm having trouble understanding your request. Could you please tell me specifically what you'd like to promote or market?",
                        QuestionType.PRODUCT_SERVICE
                    )
                state.stage = ConsultationStage.GATHERING
                state.errors = []
                logger.info("Recovered by providing user guidance")
        
        else:
            # Cannot recover, mark as failed
            state.stage = ConsultationStage.FAILED
            logger.error("Could not recover from consultation errors")
        
        # Store error handling metadata
        state.meta["error_handling"] = {
            "timestamp": datetime.now().isoformat(),
            "error_analysis": error_analysis,
            "recovery_attempted": error_analysis["can_recover"]
        }
        
        return state
        
    except Exception as e:
        logger.error(f"Error in error handling node: {str(e)}")
        state.errors.append(f"Error handling failure: {str(e)}")
        state.stage = ConsultationStage.FAILED
        return state


# === ROUTING FUNCTIONS ===

def _route_from_consultation(state: MarketingConsultantState) -> str:
    """
    Route from consultation orchestrator based on current stage and state.
    
    This function determines the next node based on the consultation stage
    and current conversation context.
    
    Routing Logic:
    - GATHERING + waiting for answer → continue_gathering
    - GATHERING + have answer → validate_completeness or ask more
    - VALIDATING → validate_completeness
    - READY → prepare_campaign
    - FAILED → handle_error
    
    Args:
        state: Current consultation state
        
    Returns:
        String indicating next node to execute
    """
    # Handle error states first
    if state.stage == ConsultationStage.FAILED or state.errors:
        return "handle_error"
    
    # Handle completion
    if state.stage == ConsultationStage.READY:
        return "prepare_campaign"
    
    if state.stage == ConsultationStage.COMPLETED:
        return "end_consultation"
    
    # Handle validation stage
    if state.stage == ConsultationStage.VALIDATING:
        return "validate_completeness"
    
    # Handle gathering stage
    if state.stage == ConsultationStage.GATHERING:
        # Check if we're waiting for user input - END and wait for user
        if state.is_waiting_for_answer():
            return "end_consultation"
        
        # Check if we should validate completeness
        # Move to validation if we have core information OR enough questions
        core_fields = ["goal", "audience", "channels"]  # Budget is helpful but not critical
        has_core_info = all(state.parsed_intent.get(field) for field in core_fields)
        
        if has_core_info or state.question_count >= 3:
            return "validate_completeness"
        
        # Check if we've reached max questions limit
        if state.question_count >= state.max_questions:
            return "validate_completeness"
        
        # Continue with more questions (this should ask a question and then wait)
        return "continue_gathering"
    
    # Initial stage should move to gathering
    if state.stage == ConsultationStage.INITIAL:
        state.stage = ConsultationStage.GATHERING
        return "continue_gathering"
    
    # Default: validate what we have
    return "validate_completeness"


def _route_from_answer_processing(state: MarketingConsultantState) -> str:
    """Route from answer processing based on processing results."""
    # Check for errors
    if state.errors:
        return "handle_error"
    
    # Check processing metadata for recommendations
    processing_meta = state.meta.get("last_answer_processing", {})
    next_action = processing_meta.get("next_action")
    
    if next_action == "validate_completeness":
        return "validate_completeness"
    elif next_action == "clarify_response":
        return "back_to_consultation"
    
    # Smart routing based on state
    # Move to validation if we have core information OR enough questions
    core_fields = ["goal", "audience", "channels"]  # Budget is helpful but not critical
    has_core_info = all(state.parsed_intent.get(field) for field in core_fields)
    
    if has_core_info or state.question_count >= 3:
        return "validate_completeness"
    
    # If we've reached max questions, force validation
    if state.question_count >= state.max_questions:
        return "validate_completeness"
    
    # Otherwise continue consultation 
    return "back_to_consultation"


def _route_from_completeness_evaluation(state: MarketingConsultantState) -> str:
    """Route from completeness evaluation based on evaluation results."""
    # Check for errors
    if state.errors:
        return "handle_error"
    
    # Check evaluation results
    if state.has_enough_info:
        return "ready_for_campaign"
    
    # Check if we've asked too many questions
    if state.question_count >= state.max_questions:
        # Force readiness to avoid infinite loops
        state.has_enough_info = True
        return "ready_for_campaign"
    
    # Need more information
    return "ask_more_questions"


def _route_from_error_handling(state: MarketingConsultantState) -> str:
    """Route from error handling based on recovery success."""
    # Check if recovery was successful
    error_meta = state.meta.get("error_handling", {})
    
    if error_meta.get("recovery_attempted", False) and state.stage != ConsultationStage.FAILED:
        return "retry_consultation"
    else:
        return "end_with_error"


# === HELPER FUNCTIONS ===

def _finalize_intent_formatting(state: MarketingConsultantState) -> None:
    """
    Finalize parsed intent formatting for compatibility with campaign graphs.
    
    This ensures that the consultation results are properly formatted
    for integration with existing campaign creation workflows.
    """
    # Ensure all required fields have some value
    defaults = {
        "goal": state.user_input,
        "audience": "general audience",
        "budget": "not specified",
        "channels": "Email, Instagram",  # Default channels as string
        "tone": "professional",
        "timeline": "when ready"
    }
    
    for field, default_value in defaults.items():
        if not state.parsed_intent.get(field):
            state.parsed_intent[field] = default_value
    
    # Ensure channels has a default value if not set
    if not state.parsed_intent.get("channels"):
        state.parsed_intent["channels"] = "Email, Instagram"


def _generate_final_consultation_summary(state: MarketingConsultantState) -> str:
    """Generate a comprehensive summary of the consultation process."""
    summary_lines = [
        "=== MARKETING CONSULTATION SUMMARY ===",
        f"Session ID: {state.session_id}",
        f"Original Request: '{state.user_input}'",
        f"Questions Asked: {state.question_count}",
        f"Consultation Duration: {_calculate_consultation_duration(state)}",
        "",
        "=== CAMPAIGN REQUIREMENTS ===",
    ]
    
    for key, value in state.parsed_intent.items():
        if value:
            formatted_key = key.replace("_", " ").title()
            if isinstance(value, list):
                summary_lines.append(f"{formatted_key}: {', '.join(value)}")
            else:
                summary_lines.append(f"{formatted_key}: {value}")
    
    if state.qa_history:
        summary_lines.extend([
            "",
            "=== CONSULTATION CONVERSATION ===",
        ])
        
        for i, qa in enumerate(state.qa_history, 1):
            summary_lines.append(f"Q{i}: {qa['question']}")
            if qa.get("answer"):
                summary_lines.append(f"A{i}: {qa['answer']}")
            summary_lines.append("")
    
    # Add quality metrics
    metrics = state.meta.get("consultation_metrics", {})
    if metrics:
        summary_lines.extend([
            "=== CONSULTATION METRICS ===",
            f"Information Completeness: {metrics.get('completeness_score', 'N/A')}",
            f"Average Response Quality: {metrics.get('avg_response_quality', 'N/A')}",
            f"Consultation Efficiency: {metrics.get('efficiency_score', 'N/A')}",
        ])
    
    return "\n".join(summary_lines)


def _calculate_consultation_duration(state: MarketingConsultantState) -> str:
    """Calculate and format consultation duration."""
    if not state.timestamp:
        return "Unknown"
    
    duration = datetime.now() - state.timestamp
    minutes = duration.total_seconds() / 60
    
    if minutes < 1:
        return f"{int(duration.total_seconds())} seconds"
    elif minutes < 60:
        return f"{int(minutes)} minutes"
    else:
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        return f"{hours}h {remaining_minutes}m"


def _calculate_consultation_metrics(state: MarketingConsultantState) -> Dict[str, Any]:
    """Calculate analytics metrics for the consultation process."""
    metrics = {}
    
    # Information completeness score
    filled_fields = sum(1 for v in state.parsed_intent.values() if v)
    total_fields = len(state.parsed_intent)
    metrics["completeness_score"] = filled_fields / total_fields if total_fields > 0 else 0
    
    # Average response quality (from processing metadata)
    quality_scores = []
    for qa in state.qa_history:
        # This would be populated by answer processing
        processing_meta = state.meta.get(f"processing_{qa.get('question', '')}", {})
        quality = processing_meta.get("quality_assessment", {}).get("overall_score")
        if quality is not None:
            quality_scores.append(quality)
    
    metrics["avg_response_quality"] = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
    
    # Efficiency score (information gathered per question)
    metrics["efficiency_score"] = filled_fields / state.question_count if state.question_count > 0 else 0
    
    # Duration metrics
    if state.timestamp:
        duration_minutes = (datetime.now() - state.timestamp).total_seconds() / 60
        metrics["duration_minutes"] = duration_minutes
        metrics["questions_per_minute"] = state.question_count / duration_minutes if duration_minutes > 0 else 0
    
    return metrics


def _analyze_consultation_errors(state: MarketingConsultantState) -> Dict[str, Any]:
    """
    Analyze consultation errors and determine recovery strategies.
    
    Args:
        state: Consultation state with error information
        
    Returns:
        Dict with error analysis and recovery recommendations
    """
    error_types = []
    recovery_possible = True
    recovery_action = "retry_last_action"
    
    for error in state.errors:
        if "LLM" in error or "evaluation" in error:
            error_types.append("llm_failure")
        elif "processing" in error:
            error_types.append("processing_failure")
        elif "state" in error or "corruption" in error:
            error_types.append("state_corruption")
        else:
            error_types.append("unknown_error")
    
    # Determine recovery strategy based on error types
    if "state_corruption" in error_types:
        recovery_action = "reset_to_gathering"
    elif "llm_failure" in error_types and len(state.qa_history) < 2:
        recovery_action = "provide_guidance"
    elif len(state.errors) > 3:
        # Too many errors, cannot recover
        recovery_possible = False
        recovery_action = "escalate_to_human"
    
    return {
        "error_types": error_types,
        "can_recover": recovery_possible,
        "recovery_action": recovery_action,
        "error_count": len(state.errors),
        "consultation_salvageable": bool(state.parsed_intent) and any(state.parsed_intent.values())
    }
