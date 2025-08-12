"""
Answer Processor - Extract and Validate User Responses

This module handles processing and validation of user responses during
the stateful marketing consultation flow. It extracts relevant information
and updates the consultation state appropriately.

Key Features:
- Intelligent extraction of information from natural language responses
- Context-aware parsing based on question type and conversation history
- Quality validation and feedback for incomplete or unclear responses
- Structured updating of consultation state with extracted information

Architecture Benefits:
- Handles natural conversation patterns (users don't always answer directly)
- Extracts multiple pieces of information from single responses
- Provides feedback loop for answer quality improvement
- Maintains conversation context for better extraction accuracy

Integration:
- Used by marketing_consultant_node to process each user response
- Updates parsed_intent based on extracted information
- Provides quality feedback to guide follow-up questions
"""

import re
from typing import Dict, List, Optional, Any, Tuple

from src.utils.marketing_state import (
    MarketingConsultantState, 
    QuestionType
)
import logging

logger = logging.getLogger(__name__)


def process_user_answer(
    state: MarketingConsultantState, 
    user_response: str
) -> Dict[str, Any]:
    """
    Process a user's response and extract relevant information.
    
    This function analyzes the user's response in context of the conversation
    and extracts structured information to update the consultation state.
    
    Args:
        state: Current consultation state with conversation history
        user_response: The user's latest response to process
        
    Returns:
        Dict containing:
        - extracted_info: Information extracted from the response
        - quality_assessment: Quality analysis of the response
        - next_action: Recommended next action (continue, clarify, etc.)
        - updated_intent: Suggested updates to parsed_intent
        
    Example:
        User response: "I want to promote my coffee shop to local professionals with a $2000 budget"
        Returns: {
            "extracted_info": {
                "goal": "promote coffee shop",
                "audience": "local professionals", 
                "budget": "$2000"
            },
            "quality_assessment": {"overall_score": 0.9, "completeness": "high"},
            "next_action": "continue_questioning",
            "updated_intent": {...}
        }
    """
    logger.debug(f"Processing user response: '{user_response[:50]}...'")
    
    if not user_response or not user_response.strip():
        return _handle_empty_response()
    
    # Get context from the last question asked
    question_context = _get_last_question_context(state)
    
    # Extract information based on question context and response content
    extracted_info = _extract_information_from_response(
        user_response, 
        question_context, 
        state
    )
    
    # Assess response quality
    quality_assessment = _assess_response_quality(
        user_response, 
        question_context, 
        extracted_info
    )
    
    # Determine next action based on extraction and quality
    next_action = _determine_next_action(
        extracted_info, 
        quality_assessment, 
        state
    )
    
    # Create updated intent incorporating extracted information
    updated_intent = _create_updated_intent(state, extracted_info)
    
    result = {
        "extracted_info": extracted_info,
        "quality_assessment": quality_assessment,
        "next_action": next_action,
        "updated_intent": updated_intent,
        "processing_metadata": {
            "response_length": len(user_response),
            "question_context": question_context,
            "extraction_confidence": quality_assessment.get("extraction_confidence", 0.5)
        }
    }
    
    logger.info(f"Processed response: extracted {len(extracted_info)} fields, quality score: {quality_assessment.get('overall_score', 0)}")
    return result


def _handle_empty_response() -> Dict[str, Any]:
    """Handle cases where user provides no response."""
    return {
        "extracted_info": {},
        "quality_assessment": {
            "overall_score": 0.0,
            "issues": ["no_response"],
            "recommendations": ["Please provide a response to continue"]
        },
        "next_action": "request_response",
        "updated_intent": {},
        "processing_metadata": {
            "response_length": 0,
            "question_context": None,
            "extraction_confidence": 0.0
        }
    }


def _get_last_question_context(state: MarketingConsultantState) -> Optional[Dict[str, str]]:
    """
    Get context from the last question asked.
    
    This helps understand what type of information the user is likely
    providing in their response.
    
    Args:
        state: Current consultation state
        
    Returns:
        Dict with question context or None if no questions asked
    """
    if not state.qa_history:
        return None
    
    last_qa = state.qa_history[-1]
    return {
        "question": last_qa.get("question", ""),
        "question_type": last_qa.get("question_type", ""),
        "expected_info": _map_question_type_to_expected_info(last_qa.get("question_type", ""))
    }


def _map_question_type_to_expected_info(question_type: str) -> List[str]:
    """Map question types to expected information types in responses."""
    mapping = {
        QuestionType.PRODUCT_SERVICE.value: ["goal", "product", "service"],
        QuestionType.TARGET_AUDIENCE.value: ["audience", "demographics", "target"],
        QuestionType.BUDGET.value: ["budget", "cost", "spending"],
        QuestionType.CHANNELS.value: ["channels", "platforms", "media"],
        QuestionType.TONE_STYLE.value: ["tone", "style", "voice"],
        QuestionType.TIMELINE.value: ["timeline", "date", "schedule"],
        QuestionType.GOALS_METRICS.value: ["goals", "metrics", "success"],
        QuestionType.CONSTRAINTS.value: ["constraints", "requirements", "limitations"]
    }
    return mapping.get(question_type, ["general"])


def _extract_information_from_response(
    response: str, 
    question_context: Optional[Dict], 
    state: MarketingConsultantState
) -> Dict[str, str]:
    """
    Extract structured information from user response.
    
    This uses pattern matching and context awareness to pull out
    specific pieces of information that can update our consultation state.
    
    Args:
        response: User's response text
        question_context: Context of the question being answered
        state: Current consultation state for additional context
        
    Returns:
        Dict mapping information types to extracted values
    """
    extracted = {}
    response_lower = response.lower().strip()
    
    # If we have question context, prioritize that type of extraction
    if question_context:
        primary_extraction = _extract_by_question_type(
            response, 
            question_context.get("question_type", "")
        )
        extracted.update(primary_extraction)
    
    # Always try to extract other information opportunistically
    # Users often provide more info than asked for
    
    # Extract goal/product information
    goal_info = _extract_goal_information(response)
    if goal_info:
        extracted["goal"] = goal_info
    
    # Extract audience information
    audience_info = _extract_audience_information(response)
    if audience_info:
        extracted["audience"] = audience_info
    
    # Extract budget information
    budget_info = _extract_budget_information(response)
    if budget_info:
        extracted["budget"] = budget_info
    
    # Extract channel information
    channel_info = _extract_channel_information(response)
    if channel_info:
        extracted["channels"] = channel_info
    
    # Extract tone/style information
    tone_info = _extract_tone_information(response)
    if tone_info:
        extracted["tone"] = tone_info
    
    # Extract timeline information
    timeline_info = _extract_timeline_information(response)
    if timeline_info:
        extracted["timeline"] = timeline_info
    
    return extracted


def _extract_by_question_type(response: str, question_type: str) -> Dict[str, str]:
    """
    Extract information specifically for the question type asked.
    
    This focuses extraction on the most likely information type
    based on what question was asked.
    """
    if question_type == QuestionType.PRODUCT_SERVICE.value:
        goal = _extract_goal_information(response)
        return {"goal": goal} if goal else {}
    
    elif question_type == QuestionType.TARGET_AUDIENCE.value:
        audience = _extract_audience_information(response)
        return {"audience": audience} if audience else {}
    
    elif question_type == QuestionType.BUDGET.value:
        budget = _extract_budget_information(response)
        return {"budget": budget} if budget else {}
    
    elif question_type == QuestionType.CHANNELS.value:
        channels = _extract_channel_information(response)
        return {"channels": channels} if channels else {}
    
    elif question_type == QuestionType.TONE_STYLE.value:
        tone = _extract_tone_information(response)
        return {"tone": tone} if tone else {}
    
    elif question_type == QuestionType.TIMELINE.value:
        timeline = _extract_timeline_information(response)
        return {"timeline": timeline} if timeline else {}
    
    else:
        # For unknown types, return the response as-is
        return {"general": response.strip()}


def _extract_goal_information(response: str) -> Optional[str]:
    """Extract goal/product/service information from response."""
    response_lower = response.lower().strip()
    
    # Pattern 1: Direct statements
    patterns = [
        r'(?:promote|market|advertise|sell)\s+(?:my\s+)?(.+?)(?:\s+to|\s+for|\s+on|$)',
        r'(?:it\'s|its)\s+(?:a\s+)?(.+?)(?:\s+for|\s+that|$)',
        r'(?:we|i)\s+(?:sell|offer|provide|make)\s+(.+?)(?:\s+to|\s+for|$)',
        r'(?:a|an)\s+(.+?)(?:\s+(?:business|service|product|app|website))',
        r'^(.+?)(?:\s+(?:business|service|product|app|website|shop|store))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response_lower)
        if match:
            goal = match.group(1).strip()
            # Filter out generic terms
            if len(goal) > 2 and goal not in ['my', 'our', 'the', 'this', 'that']:
                return goal
    
    # Pattern 2: If response is short and descriptive, use as-is
    if len(response.strip()) < 50 and not any(word in response_lower for word in ['?', 'what', 'how', 'when']):
        return response.strip()
    
    return None


def _extract_audience_information(response: str) -> Optional[str]:
    """Extract target audience information from response."""
    response_lower = response.lower().strip()
    
    # Pattern 1: Explicit audience mentions
    patterns = [
        r'(?:target|targeting|for)\s+(.+?)(?:\s+(?:aged|between|who|that)|$)',
        r'(?:to|for)\s+(.+?)(?:\s+(?:aged|between|in|on)|$)',
        r'(?:audience|customers?|users?|people)\s+(?:are|is)?\s*(.+?)(?:\s+(?:aged|who|that)|$)',
        r'(?:aged?|between)\s+(.+?)(?:\s+(?:years?|and|to)|$)',
        r'(?:young|old|senior|middle-aged)\s+(.+?)(?:\s|$)',
        r'(.+?)(?:\s+(?:professionals?|students?|seniors?|teenagers?|millennials?))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response_lower)
        if match:
            audience = match.group(1).strip()
            # Filter out generic terms
            generic_terms = ['people', 'everyone', 'anybody', 'users', 'customers', 'the']
            if audience and audience not in generic_terms and len(audience) > 2:
                return audience
    
    # Pattern 2: Demographic descriptors
    demographic_patterns = [
        r'\b(teenagers?|teens?)\b',
        r'\b(millennials?|gen\s*z|boomers?)\b',
        r'\b(students?|professionals?|seniors?)\b',
        r'\b(young\s+\w+|middle-aged\s+\w+|older\s+\w+)\b',
        r'\b(local\s+\w+|urban\s+\w+|rural\s+\w+)\b',
    ]
    
    for pattern in demographic_patterns:
        match = re.search(pattern, response_lower)
        if match:
            return match.group(1)
    
    return None


def _extract_budget_information(response: str) -> Optional[str]:
    """Extract budget information from response."""
    response_lower = response.lower().strip()
    
    # Pattern 1: Direct monetary amounts
    money_patterns = [
        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
        r'\b(\d{1,3}(?:,\d{3})*)\s*(?:dollars?|bucks?)\b',
        r'\b(\d+)\s*k\b',  # 5k, 10k, etc.
        r'\b(\d+)\s*thousand\b',
    ]
    
    for pattern in money_patterns:
        match = re.search(pattern, response_lower)
        if match:
            amount = match.group(1)
            if 'k' in response_lower:
                return f"${amount}k"
            elif 'thousand' in response_lower:
                return f"${amount},000"
            else:
                return f"${amount}"
    
    # Pattern 2: Budget ranges and qualifiers
    range_patterns = [
        r'\b(under|below|less than)\s+\$?(\d+)(?:k|,\d{3})*\b',
        r'\b(over|above|more than)\s+\$?(\d+)(?:k|,\d{3})*\b',
        r'\b(around|about|approximately)\s+\$?(\d+)(?:k|,\d{3})*\b',
        r'\bbetween\s+\$?(\d+)(?:k|,\d{3})*\s+(?:and|to)\s+\$?(\d+)(?:k|,\d{3})*\b',
    ]
    
    for pattern in range_patterns:
        match = re.search(pattern, response_lower)
        if match:
            qualifier = match.group(1)
            amount = match.group(2)
            return f"{qualifier} ${amount}"
    
    # Pattern 3: Budget descriptors
    descriptor_patterns = [
        r'\b(small|limited|tight|minimal)\s+budget\b',
        r'\b(large|big|substantial|significant)\s+budget\b',
        r'\b(monthly|weekly|annual|yearly)\s+budget\b',
    ]
    
    for pattern in descriptor_patterns:
        match = re.search(pattern, response_lower)
        if match:
            return match.group(1) + " budget"
    
    return None


def _extract_channel_information(response: str) -> Optional[str]:
    """Extract marketing channel preferences from response."""
    response_lower = response.lower().strip()
    
    # Known marketing channels
    channels = {
        'instagram': ['instagram', 'insta', 'ig'],
        'facebook': ['facebook', 'fb'],
        'twitter': ['twitter', 'x'],
        'linkedin': ['linkedin'],
        'email': ['email', 'email marketing', 'newsletters'],
        'google ads': ['google ads', 'google advertising', 'adwords'],
        'youtube': ['youtube', 'video'],
        'tiktok': ['tiktok', 'tik tok'],
        'local': ['local', 'local advertising', 'community'],
        'social media': ['social media', 'social'],
    }
    
    found_channels = []
    for channel, aliases in channels.items():
        for alias in aliases:
            if alias in response_lower:
                found_channels.append(channel)
                break
    
    if found_channels:
        # Remove duplicates and generic terms if specific ones exist
        if 'social media' in found_channels and len(found_channels) > 1:
            found_channels.remove('social media')
        
        return ', '.join(found_channels)
    
    # Look for channel-related patterns
    channel_patterns = [
        r'\b(online|digital|internet)\s+(?:marketing|advertising)\b',
        r'\b(print|newspaper|radio|tv)\s+(?:advertising|ads)\b',
        r'\b(word of mouth|referrals?)\b',
    ]
    
    for pattern in channel_patterns:
        match = re.search(pattern, response_lower)
        if match:
            return match.group(0)
    
    return None


def _extract_tone_information(response: str) -> Optional[str]:
    """Extract tone/style preferences from response."""
    response_lower = response.lower().strip()
    
    # Tone descriptors
    tone_patterns = [
        r'\b(professional|business|formal|serious)\b',
        r'\b(casual|friendly|relaxed|informal)\b',
        r'\b(fun|playful|energetic|exciting)\b',
        r'\b(elegant|sophisticated|premium|luxury)\b',
        r'\b(authentic|genuine|honest|transparent)\b',
        r'\b(modern|trendy|hip|contemporary)\b',
        r'\b(traditional|classic|timeless|conservative)\b',
    ]
    
    found_tones = []
    for pattern in tone_patterns:
        matches = re.findall(pattern, response_lower)
        found_tones.extend(matches)
    
    if found_tones:
        # Remove duplicates and return combined
        unique_tones = list(dict.fromkeys(found_tones))  # Preserve order
        return ', '.join(unique_tones)
    
    return None


def _extract_timeline_information(response: str) -> Optional[str]:
    """Extract timeline/schedule information from response."""
    response_lower = response.lower().strip()
    
    # Timeline patterns
    timeline_patterns = [
        r'\b(asap|immediately|right away|soon)\b',
        r'\b(next week|this week|next month|this month)\b',
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
        r'\b(spring|summer|fall|autumn|winter)\b',
        r'\b(holiday|christmas|new year|valentine|easter)\b',
        r'\bin\s+(\d+)\s+(days?|weeks?|months?)\b',
        r'\bby\s+([\w\s]+?)\b(?:\s|$)',
    ]
    
    for pattern in timeline_patterns:
        match = re.search(pattern, response_lower)
        if match:
            if pattern.endswith(r'\bby\s+([\w\s]+?)\b(?:\s|$)'):
                return f"by {match.group(1)}"
            else:
                return match.group(0)
    
    return None


def _assess_response_quality(
    response: str, 
    question_context: Optional[Dict], 
    extracted_info: Dict[str, str]
) -> Dict[str, Any]:
    """
    Assess the quality and completeness of the user's response.
    
    This evaluates how well the response answers the question and
    provides useful information for campaign planning.
    """
    quality_factors = {
        "length_score": _score_response_length(response),
        "specificity_score": _score_response_specificity(response, extracted_info),
        "relevance_score": _score_response_relevance(response, question_context),
        "extraction_confidence": _calculate_extraction_confidence(extracted_info),
    }
    
    # Calculate overall quality score
    overall_score = sum(quality_factors.values()) / len(quality_factors)
    
    # Identify issues and recommendations
    issues = []
    recommendations = []
    
    if quality_factors["length_score"] < 0.3:
        issues.append("response_too_brief")
        recommendations.append("Please provide more details")
    
    if quality_factors["specificity_score"] < 0.3:
        issues.append("response_too_generic")
        recommendations.append("Please be more specific")
    
    if quality_factors["relevance_score"] < 0.5:
        issues.append("response_not_relevant")
        recommendations.append("Please focus on the question asked")
    
    if quality_factors["extraction_confidence"] < 0.3:
        issues.append("unclear_information")
        recommendations.append("Please clarify your response")
    
    return {
        "overall_score": overall_score,
        "quality_factors": quality_factors,
        "issues": issues,
        "recommendations": recommendations,
        "is_adequate": overall_score >= 0.6 and len(issues) <= 1,
        "needs_clarification": overall_score < 0.4 or "unclear_information" in issues
    }


def _score_response_length(response: str) -> float:
    """Score response based on length (0-1)."""
    length = len(response.strip())
    if length < 3:
        return 0.0
    elif length < 10:
        return 0.3
    elif length < 25:
        return 0.7
    else:
        return 1.0


def _score_response_specificity(response: str, extracted_info: Dict[str, str]) -> float:
    """Score response based on specificity indicators."""
    specificity_indicators = [
        r'\d+',  # Numbers
        r'\b(?:specific|exactly|precisely)\b',  # Specificity words
        r'\b(?:aged?|between|from|to)\s+\d+',  # Age ranges
        r'\$\d+',  # Dollar amounts
        r'\b(?:daily|weekly|monthly|annually)\b',  # Time specificity
    ]
    
    score = 0.3  # Base score
    for pattern in specificity_indicators:
        if re.search(pattern, response, re.IGNORECASE):
            score += 0.2
    
    # Bonus for extracting multiple pieces of info
    if len(extracted_info) > 1:
        score += 0.1 * len(extracted_info)
    
    return min(score, 1.0)


def _score_response_relevance(response: str, question_context: Optional[Dict]) -> float:
    """Score response relevance to the question asked."""
    if not question_context:
        return 0.7  # Neutral score if no context
    
    expected_info = question_context.get("expected_info", [])
    response_lower = response.lower()
    
    relevance_score = 0.5  # Base score
    
    # Check if response contains expected information types
    for info_type in expected_info:
        if info_type in response_lower:
            relevance_score += 0.2
    
    # Check for question-answering patterns
    answer_patterns = [
        r'\b(yes|no|maybe|sure|okay)\b',
        r'\b(i want|i need|i prefer)\b',
        r'\b(my|our|the|this|that)\b',
    ]
    
    for pattern in answer_patterns:
        if re.search(pattern, response_lower):
            relevance_score += 0.1
            break
    
    return min(relevance_score, 1.0)


def _calculate_extraction_confidence(extracted_info: Dict[str, str]) -> float:
    """Calculate confidence in information extraction."""
    if not extracted_info:
        return 0.0
    
    # Base confidence
    confidence = 0.5
    
    # Higher confidence for more extractions
    confidence += 0.1 * len(extracted_info)
    
    # Higher confidence for longer extracted values
    avg_length = sum(len(v) for v in extracted_info.values()) / len(extracted_info)
    if avg_length > 10:
        confidence += 0.2
    elif avg_length > 5:
        confidence += 0.1
    
    return min(confidence, 1.0)


def _determine_next_action(
    extracted_info: Dict[str, str], 
    quality_assessment: Dict[str, Any], 
    state: MarketingConsultantState
) -> str:
    """
    Determine the recommended next action based on extraction and quality.
    
    Returns action codes:
    - "continue_questioning": Normal flow, ask next question
    - "clarify_response": Response unclear, ask for clarification
    - "validate_completeness": Good info, check if ready for campaign
    - "request_response": No response received
    """
    if not extracted_info and quality_assessment["overall_score"] < 0.3:
        return "clarify_response"
    
    if quality_assessment.get("needs_clarification", False):
        return "clarify_response"
    
    if state.question_count >= 4 and extracted_info:
        return "validate_completeness"
    
    if quality_assessment["is_adequate"] and extracted_info:
        return "continue_questioning"
    
    return "clarify_response"


def _create_updated_intent(
    state: MarketingConsultantState, 
    extracted_info: Dict[str, str]
) -> Dict[str, Optional[str]]:
    """
    Create updated parsed_intent by merging current state with extracted info.
    
    This preserves existing information while incorporating new extractions.
    """
    # Start with current parsed intent
    updated_intent = state.parsed_intent.copy()
    
    # Update with extracted information
    for key, value in extracted_info.items():
        if value and value.strip():
            # Only update if we don't have this info or new info is more specific
            current_value = updated_intent.get(key, "")
            if not current_value or len(value) > len(current_value):
                updated_intent[key] = value.strip()
    
    return updated_intent
