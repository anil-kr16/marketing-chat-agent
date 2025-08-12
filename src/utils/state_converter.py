"""
State Converter - Bridge Between Consultation and Campaign States

This module provides conversion utilities between the new MarketingConsultantState
used for stateful consultations and the existing MessagesState used by campaign
creation graphs, ensuring seamless integration with existing workflows.

Key Features:
- Bidirectional conversion between consultation and campaign states
- Information preservation during state transitions
- Compatibility layer for existing campaign creation nodes
- Metadata transfer for analytics and debugging continuity

Architecture Benefits:
- Enables gradual migration to stateful consultation without breaking changes
- Preserves all conversation context and gathered information
- Maintains backward compatibility with existing campaign graphs
- Provides clear integration points for different conversation modes

Integration Strategy:
- Used by runnable scripts to bridge consultation and campaign phases
- Enables existing campaign nodes to work with consultation-gathered data
- Preserves session information for analytics and user experience tracking
- Provides fallback compatibility for mixed conversation patterns

Conversion Patterns:
1. Consultation → Campaign: When consultation is complete and ready for execution
2. Campaign → Consultation: When campaign needs more information (rare)
3. Preservation: Metadata and context preservation across conversions
4. Validation: Ensuring converted states meet target format requirements
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage

from src.utils.marketing_state import MarketingConsultantState, ConsultationStage
from src.utils.state import MessagesState
import logging

logger = logging.getLogger(__name__)


def consultant_to_campaign_state(
    consultant_state: MarketingConsultantState,
    preserve_conversation: bool = True
) -> MessagesState:
    """
    Convert MarketingConsultantState to MessagesState for campaign creation.
    
    This is the primary conversion used when a consultation is complete
    and ready to hand off to existing campaign creation workflows.
    
    Args:
        consultant_state: Completed consultation state with gathered information
        preserve_conversation: Whether to include conversation history in messages
        
    Returns:
        MessagesState compatible with existing campaign creation graphs
        
    Example:
        consultation_complete = MarketingConsultantState(...)
        campaign_state = consultant_to_campaign_state(consultation_complete)
        # campaign_state can now be used with existing FullMarketingAgent
    """
    logger.info(f"Converting consultation state to campaign state: {consultant_state.session_id}")
    
    try:
        # Create base campaign state
        campaign_state = MessagesState()
        
        # === CORE INFORMATION TRANSFER ===
        
        # Transfer parsed intent (this is the main payload)
        campaign_state["parsed_intent"] = _format_intent_for_campaign(consultant_state.parsed_intent)
        
        # === MESSAGE HISTORY CREATION ===
        
        messages = []
        
        # Add system message for context
        if preserve_conversation:
            system_content = _create_system_context_message(consultant_state)
            messages.append(SystemMessage(content=system_content))
        
        # Add user's original request
        original_request = consultant_state.user_input
        messages.append(HumanMessage(content=original_request))
        
        # Add conversation history if requested
        if preserve_conversation and consultant_state.qa_history:
            conversation_messages = _convert_qa_history_to_messages(consultant_state.qa_history)
            messages.extend(conversation_messages)
        
        # Add final AI message indicating readiness for campaign
        if consultant_state.final_plan:
            final_message = f"""Based on our consultation, I understand you want to:

{consultant_state.final_plan}

I'm now ready to create your marketing campaign with this information."""
            messages.append(AIMessage(content=final_message))
        
        campaign_state["messages"] = messages
        
        # === METADATA TRANSFER ===
        
        # Transfer consultation metadata for analytics and debugging
        campaign_meta = {
            "consultation_session_id": consultant_state.session_id,
            "consultation_completed_at": datetime.now().isoformat(),
            "consultation_duration": _calculate_consultation_duration(consultant_state),
            "questions_asked": consultant_state.question_count,
            "consultation_stage": consultant_state.stage.value if consultant_state.stage else "unknown",
            "information_completeness": _calculate_information_completeness(consultant_state),
            "original_user_input": consultant_state.user_input,
        }
        
        # Merge with existing meta or create new
        existing_meta = consultant_state.meta or {}
        campaign_meta.update(existing_meta)
        campaign_state["meta"] = campaign_meta
        
        # === AGENT FLAGS FOR FLOW CONTROL ===
        
        # Set flags to indicate this came from consultation
        campaign_state["agent_flags"] = {
            "from_consultation": True,
            "consultation_complete": True,
            "skip_intent_parsing": True,  # We already have structured intent
            "ready_for_execution": True
        }
        
        logger.info(f"Successfully converted consultation to campaign state")
        return campaign_state
        
    except Exception as e:
        logger.error(f"Error converting consultation to campaign state: {str(e)}")
        # Return minimal campaign state as fallback
        return _create_fallback_campaign_state(consultant_state, str(e))


def campaign_to_consultant_state(
    campaign_state: MessagesState,
    session_id: Optional[str] = None
) -> MarketingConsultantState:
    """
    Convert MessagesState to MarketingConsultantState for consultation.
    
    This is used when an existing campaign workflow needs to gather
    more information or when resuming an interrupted consultation.
    
    Args:
        campaign_state: Existing campaign state to convert
        session_id: Optional session ID for the new consultation
        
    Returns:
        MarketingConsultantState ready for continued consultation
        
    Example:
        # When campaign creation needs more info
        campaign_state = existing_campaign_state
        consultation_state = campaign_to_consultant_state(campaign_state)
        # Continue with consultation to gather missing information
    """
    logger.info("Converting campaign state to consultation state")
    
    try:
        # Extract user input from messages
        user_input = _extract_user_input_from_messages(campaign_state.get("messages", []))
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create consultation state
        consultant_state = MarketingConsultantState(
            user_input=user_input,
            session_id=session_id,
            timestamp=datetime.now(),
            stage=ConsultationStage.GATHERING  # Assume we need more info
        )
        
        # Transfer parsed intent if available
        existing_intent = campaign_state.get("parsed_intent", {})
        if existing_intent:
            consultant_state.parsed_intent = _format_intent_for_consultation(existing_intent)
        
        # Reconstruct conversation history if possible
        messages = campaign_state.get("messages", [])
        qa_history = _extract_qa_history_from_messages(messages)
        consultant_state.qa_history = qa_history
        consultant_state.question_count = len(qa_history)
        
        # Transfer metadata
        existing_meta = campaign_state.get("meta", {})
        consultant_state.meta = {
            "converted_from_campaign": True,
            "conversion_timestamp": datetime.now().isoformat(),
            "original_campaign_meta": existing_meta
        }
        
        logger.info(f"Successfully converted campaign to consultation state: {session_id}")
        return consultant_state
        
    except Exception as e:
        logger.error(f"Error converting campaign to consultation state: {str(e)}")
        # Return minimal consultation state as fallback
        return _create_fallback_consultation_state(campaign_state, str(e))


def preserve_consultation_context(
    consultant_state: MarketingConsultantState,
    campaign_result: MessagesState
) -> MessagesState:
    """
    Preserve consultation context in campaign results.
    
    This adds consultation metadata to campaign results for
    analytics, debugging, and user experience continuity.
    
    Args:
        consultant_state: Original consultation state
        campaign_result: Campaign creation results
        
    Returns:
        Campaign result with consultation context preserved
    """
    logger.debug("Preserving consultation context in campaign results")
    
    # Ensure meta exists
    if "meta" not in campaign_result:
        campaign_result["meta"] = {}
    
    # Add consultation context
    consultation_context = {
        "consultation_session_id": consultant_state.session_id,
        "consultation_start": consultant_state.timestamp.isoformat() if consultant_state.timestamp else None,
        "consultation_questions": consultant_state.question_count,
        "consultation_stage": consultant_state.stage.value if consultant_state.stage else "unknown",
        "user_original_input": consultant_state.user_input,
        "consultation_qa_summary": _create_qa_summary(consultant_state.qa_history)
    }
    
    campaign_result["meta"]["consultation_context"] = consultation_context
    
    return campaign_result


def validate_state_conversion(
    source_state: Any,
    target_state: Any,
    conversion_type: str
) -> Dict[str, Any]:
    """
    Validate that state conversion preserved important information.
    
    This provides quality assurance for state conversions and
    helps identify issues with information loss or corruption.
    
    Args:
        source_state: Original state before conversion
        target_state: Converted state to validate
        conversion_type: Type of conversion performed
        
    Returns:
        Dict with validation results and any issues found
    """
    validation_result = {
        "conversion_type": conversion_type,
        "validation_timestamp": datetime.now().isoformat(),
        "success": True,
        "issues": [],
        "warnings": [],
        "preserved_fields": [],
        "lost_fields": []
    }
    
    try:
        if conversion_type == "consultation_to_campaign":
            validation_result.update(_validate_consultation_to_campaign(source_state, target_state))
        elif conversion_type == "campaign_to_consultation":
            validation_result.update(_validate_campaign_to_consultation(source_state, target_state))
        else:
            validation_result["issues"].append(f"Unknown conversion type: {conversion_type}")
            validation_result["success"] = False
    
    except Exception as e:
        validation_result["success"] = False
        validation_result["issues"].append(f"Validation error: {str(e)}")
    
    return validation_result


# === PRIVATE HELPER FUNCTIONS ===

def _format_intent_for_campaign(consultation_intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format consultation intent for campaign graph compatibility.
    
    This ensures the parsed intent from consultation is in the exact
    format expected by existing campaign creation nodes.
    """
    # Map consultation intent fields to campaign intent fields
    campaign_intent = {}
    
    # Direct mappings
    field_mappings = {
        "goal": "goal",
        "audience": "audience", 
        "budget": "budget",
        "tone": "tone",
        "timeline": "timeline"
    }
    
    for consult_field, campaign_field in field_mappings.items():
        value = consultation_intent.get(consult_field)
        if value:
            campaign_intent[campaign_field] = value
    
    # Special handling for channels (ensure list format)
    channels = consultation_intent.get("channels", [])
    if isinstance(channels, str):
        # Convert string to list
        channel_list = [c.strip().title() for c in channels.replace(",", " ").split() if c.strip()]
        campaign_intent["channels"] = channel_list if channel_list else ["Email", "Instagram"]
    elif isinstance(channels, list):
        campaign_intent["channels"] = channels
    else:
        campaign_intent["channels"] = ["Email", "Instagram"]  # Default
    
    # Ensure all required fields have some value
    defaults = {
        "goal": "marketing campaign",
        "audience": "target audience",
        "budget": "not specified",
        "tone": "professional"
    }
    
    for field, default_value in defaults.items():
        if field not in campaign_intent or not campaign_intent[field]:
            campaign_intent[field] = default_value
    
    return campaign_intent


def _format_intent_for_consultation(campaign_intent: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Format campaign intent for consultation state compatibility."""
    consultation_intent = {
        "goal": None,
        "audience": None,
        "channels": None,
        "tone": None,
        "budget": None,
        "timeline": None,
        "unique_value": None,
        "success_metrics": None
    }
    
    # Transfer available information
    for field in consultation_intent.keys():
        if field in campaign_intent:
            value = campaign_intent[field]
            if isinstance(value, list):
                consultation_intent[field] = ", ".join(str(v) for v in value)
            else:
                consultation_intent[field] = str(value) if value else None
    
    return consultation_intent


def _create_system_context_message(consultant_state: MarketingConsultantState) -> str:
    """Create system context message explaining the consultation background."""
    context_lines = [
        "CONSULTATION CONTEXT:",
        f"This campaign request came from a completed marketing consultation (Session: {consultant_state.session_id}).",
        f"The user was asked {consultant_state.question_count} clarifying questions to gather comprehensive campaign requirements.",
        "",
        "CONSULTATION SUMMARY:",
    ]
    
    if consultant_state.final_plan:
        context_lines.append(consultant_state.final_plan)
    else:
        context_lines.append("Information gathered through progressive questioning for high-quality campaign creation.")
    
    context_lines.extend([
        "",
        "IMPORTANT: All necessary information has been gathered. Proceed directly to campaign creation without additional intent parsing."
    ])
    
    return "\n".join(context_lines)


def _convert_qa_history_to_messages(qa_history: List[Dict]) -> List[BaseMessage]:
    """Convert Q&A history to message format."""
    messages = []
    
    for qa in qa_history:
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        
        if question:
            messages.append(AIMessage(content=f"Question: {question}"))
        
        if answer:
            messages.append(HumanMessage(content=f"Answer: {answer}"))
    
    return messages


def _extract_user_input_from_messages(messages: List[BaseMessage]) -> str:
    """Extract the original user input from message history."""
    for message in messages:
        if isinstance(message, HumanMessage):
            # Return first human message as original input
            content = message.content
            # Clean up if it has "Answer:" prefix
            if content.startswith("Answer:"):
                content = content[7:].strip()
            return content
    
    return "marketing request"  # Fallback


def _extract_qa_history_from_messages(messages: List[BaseMessage]) -> List[Dict]:
    """Extract Q&A history from message format."""
    qa_history = []
    current_question = None
    
    for message in messages:
        if isinstance(message, AIMessage) and message.content.startswith("Question:"):
            current_question = message.content[9:].strip()
        elif isinstance(message, HumanMessage) and message.content.startswith("Answer:"):
            answer = message.content[7:].strip()
            if current_question:
                qa_history.append({
                    "question": current_question,
                    "answer": answer,
                    "question_type": "general",
                    "timestamp": datetime.now().isoformat()
                })
                current_question = None
    
    return qa_history


def _calculate_consultation_duration(consultant_state: MarketingConsultantState) -> str:
    """Calculate consultation duration in human-readable format."""
    if not consultant_state.timestamp:
        return "unknown"
    
    duration = datetime.now() - consultant_state.timestamp
    minutes = duration.total_seconds() / 60
    
    if minutes < 1:
        return f"{int(duration.total_seconds())} seconds"
    elif minutes < 60:
        return f"{int(minutes)} minutes"
    else:
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        return f"{hours}h {remaining_minutes}m"


def _calculate_information_completeness(consultant_state: MarketingConsultantState) -> float:
    """Calculate what percentage of consultation information was gathered."""
    filled_fields = sum(1 for v in consultant_state.parsed_intent.values() if v)
    total_fields = len(consultant_state.parsed_intent)
    return filled_fields / total_fields if total_fields > 0 else 0.0


def _create_qa_summary(qa_history: List[Dict]) -> str:
    """Create a brief summary of the Q&A conversation."""
    if not qa_history:
        return "No questions asked"
    
    summary_parts = []
    for i, qa in enumerate(qa_history, 1):
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        if question and answer:
            summary_parts.append(f"Q{i}: {question[:50]}... A: {answer[:30]}...")
    
    return " | ".join(summary_parts) if summary_parts else "Questions asked but no answers recorded"


def _create_fallback_campaign_state(
    consultant_state: MarketingConsultantState, 
    error_message: str
) -> MessagesState:
    """Create minimal campaign state when conversion fails."""
    fallback_state = MessagesState()
    
    # Basic message structure
    fallback_state["messages"] = [
        HumanMessage(content=consultant_state.user_input)
    ]
    
    # Minimal parsed intent
    fallback_state["parsed_intent"] = {
        "goal": consultant_state.user_input,
        "audience": "general audience",
        "channels": ["Email", "Instagram"],
        "tone": "professional",
        "budget": "not specified"
    }
    
    # Error metadata
    fallback_state["meta"] = {
        "conversion_error": error_message,
        "fallback_conversion": True,
        "original_session_id": consultant_state.session_id
    }
    
    return fallback_state


def _create_fallback_consultation_state(
    campaign_state: MessagesState, 
    error_message: str
) -> MarketingConsultantState:
    """Create minimal consultation state when conversion fails."""
    # Extract user input if possible
    messages = campaign_state.get("messages", [])
    user_input = _extract_user_input_from_messages(messages) if messages else "marketing request"
    
    # Create minimal consultation state
    fallback_state = MarketingConsultantState(
        user_input=user_input,
        session_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.now(),
        stage=ConsultationStage.GATHERING
    )
    
    # Add error metadata
    fallback_state.meta = {
        "conversion_error": error_message,
        "fallback_conversion": True
    }
    
    return fallback_state


def _validate_consultation_to_campaign(
    consultation_state: MarketingConsultantState, 
    campaign_state: MessagesState
) -> Dict[str, Any]:
    """Validate consultation to campaign conversion."""
    validation = {
        "preserved_fields": [],
        "lost_fields": [],
        "warnings": []
    }
    
    # Check if parsed intent was preserved
    campaign_intent = campaign_state.get("parsed_intent", {})
    consultation_intent = consultation_state.parsed_intent
    
    for field, value in consultation_intent.items():
        if value and field in campaign_intent:
            validation["preserved_fields"].append(field)
        elif value:
            validation["lost_fields"].append(field)
    
    # Check if messages were created
    messages = campaign_state.get("messages", [])
    if not messages:
        validation["warnings"].append("No messages created in campaign state")
    
    # Check if consultation context was preserved
    meta = campaign_state.get("meta", {})
    if "consultation_session_id" not in meta:
        validation["warnings"].append("Consultation session ID not preserved in metadata")
    
    return validation


def _validate_campaign_to_consultation(
    campaign_state: MessagesState, 
    consultation_state: MarketingConsultantState
) -> Dict[str, Any]:
    """Validate campaign to consultation conversion."""
    validation = {
        "preserved_fields": [],
        "lost_fields": [],
        "warnings": []
    }
    
    # Check if user input was extracted
    if not consultation_state.user_input or consultation_state.user_input == "marketing request":
        validation["warnings"].append("Could not extract specific user input from campaign state")
    else:
        validation["preserved_fields"].append("user_input")
    
    # Check if intent was transferred
    campaign_intent = campaign_state.get("parsed_intent", {})
    consultation_intent = consultation_state.parsed_intent
    
    for field, value in campaign_intent.items():
        if value and field in consultation_intent and consultation_intent[field]:
            validation["preserved_fields"].append(f"intent_{field}")
        elif value:
            validation["lost_fields"].append(f"intent_{field}")
    
    return validation
