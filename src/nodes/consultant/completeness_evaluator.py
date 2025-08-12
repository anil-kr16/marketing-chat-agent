"""
Completeness Evaluator - LLM-Driven Assessment of Information Adequacy

This module uses LLM intelligence to evaluate whether we have sufficient information
to create a high-quality marketing campaign, replacing simple field checking with
context-aware assessment that considers campaign viability and quality factors.

Key Features:
- LLM-powered evaluation that considers context and campaign quality
- Identifies specific missing critical information with reasoning
- Assesses answer quality and specificity beyond just presence/absence
- Provides actionable recommendations for information gathering

Architecture Benefits:
- More intelligent than simple field validation
- Considers campaign strategy and effectiveness requirements  
- Adapts evaluation criteria based on campaign type and scope
- Provides explanations for transparency and debugging

Integration:
- Used by marketing_consultant_node during validation stage
- Provides input to question prioritization for targeted follow-ups
- Helps determine when consultation is ready for campaign creation
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple

from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from src.utils.marketing_state import (
    MarketingConsultantState, 
    QuestionType,
    ConsultationStage
)
from src.config import get_config
import logging

logger = logging.getLogger(__name__)


@traceable(name="Completeness Evaluator")
def evaluate_information_completeness(state: MarketingConsultantState) -> Dict[str, Any]:
    """
    Main function to evaluate if we have sufficient information for campaign creation.
    
    This uses LLM intelligence to assess not just whether fields are filled,
    but whether the information is sufficient for creating an effective marketing campaign.
    
    Args:
        state: Current consultation state with gathered information
        
    Returns:
        Dict containing:
        - has_enough_info: Boolean indicating readiness for campaign creation
        - missing_critical_info: List of specific information still needed
        - quality_assessment: Analysis of current information quality
        - reasoning: Explanation of the evaluation decision
        - confidence_score: How confident the evaluation is (0-1)
        
    Example Return:
        {
            "has_enough_info": False,
            "missing_critical_info": ["specific_budget_range", "target_age_demographics"],
            "quality_assessment": {
                "goal_clarity": 0.8,
                "audience_specificity": 0.4,
                "budget_adequacy": 0.2,
                "channel_appropriateness": 0.7
            },
            "reasoning": "Goal is clear but audience too generic and budget unspecified",
            "confidence_score": 0.85
        }
    """
    logger.info(f"Evaluating information completeness for session {state.session_id}")
    
    try:
        # First, do a basic information audit
        basic_audit = _perform_basic_information_audit(state)
        
        # If basic requirements aren't met, no need for LLM evaluation
        if not basic_audit["meets_minimum_requirements"]:
            return {
                "has_enough_info": False,
                "missing_critical_info": basic_audit["missing_critical"],
                "quality_assessment": basic_audit["quality_scores"],
                "reasoning": basic_audit["reasoning"],
                "confidence_score": 1.0  # High confidence in basic failures
            }
        
        # For consultation purposes, if we have core fields (goal, audience, channels), 
        # consider it sufficient to proceed, even if not perfect
        # Budget is helpful but not always critical for initial consultation
        core_fields = ["goal", "audience", "channels"]
        has_core_fields = all(state.parsed_intent.get(field) for field in core_fields)
        
        if has_core_fields:
            return {
                "has_enough_info": True,  # Allow consultation to proceed
                "missing_critical_info": [],
                "quality_assessment": basic_audit["quality_scores"],
                "reasoning": "Core information (goal, audience, channels) is available. Consultation can proceed to campaign creation.",
                "confidence_score": 0.8
            }
        
        # Use LLM for sophisticated evaluation
        llm_evaluation = _evaluate_with_llm(state)
        
        # Combine basic audit with LLM evaluation
        final_evaluation = _combine_evaluations(basic_audit, llm_evaluation, state)
        
        logger.info(f"Completeness evaluation result: {final_evaluation['has_enough_info']}")
        return final_evaluation
        
    except Exception as e:
        logger.error(f"Error in completeness evaluation: {str(e)}")
        # Fallback to conservative evaluation
        return _fallback_evaluation(state, str(e))


def _perform_basic_information_audit(state: MarketingConsultantState) -> Dict[str, Any]:
    """
    Perform basic information presence and quality audit.
    
    This checks for fundamental requirements before doing expensive LLM evaluation.
    Catches obvious missing information and very low-quality responses.
    
    Args:
        state: Current consultation state
        
    Returns:
        Dict with basic audit results
    """
    logger.debug("Performing basic information audit")
    
    # Define critical fields and their quality thresholds
    critical_fields = {
        "goal": {"min_length": 3, "avoid_terms": ["idea", "business", "thing", "stuff"]},
        "audience": {"min_length": 3, "avoid_terms": ["people", "everyone", "customers", "users"]},  # Reduced from 5 to 3
        "budget": {"min_length": 2, "avoid_terms": []},
        "channels": {"min_length": 3, "avoid_terms": []}
    }
    
    missing_critical = []
    quality_scores = {}
    
    # Evaluate each critical field
    for field, requirements in critical_fields.items():
        value = state.parsed_intent.get(field, "")
        score = _evaluate_field_quality(value, requirements)
        quality_scores[f"{field}_quality"] = score
        
        # Consider field missing if quality is too low
        if score < 0.3:  # 30% threshold for basic adequacy
            missing_critical.append(field)
    
    # Check conversation quality indicators
    avg_response_length = _calculate_average_response_length(state)
    quality_scores["response_engagement"] = min(avg_response_length / 20.0, 1.0)  # Normalize to 0-1
    
    # Determine if basic requirements are met
    meets_minimum = len(missing_critical) <= 1  # Allow one missing non-critical field
    
    # Generate reasoning
    if not meets_minimum:
        reasoning = f"Missing critical information: {', '.join(missing_critical)}"
    else:
        low_quality_fields = [field for field, score in quality_scores.items() 
                             if field.endswith('_quality') and score < 0.5]
        if low_quality_fields:
            reasoning = f"Basic requirements met but quality concerns in: {', '.join(low_quality_fields)}"
        else:
            reasoning = "Basic requirements satisfied, proceeding to detailed evaluation"
    
    return {
        "meets_minimum_requirements": meets_minimum,
        "missing_critical": missing_critical,
        "quality_scores": quality_scores,
        "reasoning": reasoning,
        "average_response_length": avg_response_length
    }


def _evaluate_field_quality(value: str, requirements: Dict[str, Any]) -> float:
    """
    Evaluate the quality of a specific field value.
    
    Args:
        value: The field value to evaluate
        requirements: Quality requirements (min_length, avoid_terms, etc.)
        
    Returns:
        Quality score from 0.0 (very poor) to 1.0 (excellent)
    """
    if not value or not value.strip():
        return 0.0
    
    value_clean = value.strip().lower()
    score = 1.0
    
    # Length penalty
    min_length = requirements.get("min_length", 1)
    if len(value_clean) < min_length:
        score *= len(value_clean) / min_length
    
    # Avoid terms penalty
    avoid_terms = requirements.get("avoid_terms", [])
    for term in avoid_terms:
        if term in value_clean:
            score *= 0.3  # Significant penalty for generic terms
    
    # Bonus for specificity
    if len(value_clean) > 20:  # Detailed responses
        score = min(score * 1.2, 1.0)
    
    return score


def _calculate_average_response_length(state: MarketingConsultantState) -> float:
    """
    Calculate average length of user responses to gauge engagement.
    
    Args:
        state: Consultation state with conversation history
        
    Returns:
        Average response length in characters
    """
    if not state.qa_history:
        return 0.0
    
    response_lengths = []
    for qa in state.qa_history:
        if qa.get("answer"):
            response_lengths.append(len(qa["answer"].strip()))
    
    return sum(response_lengths) / len(response_lengths) if response_lengths else 0.0


def _evaluate_with_llm(state: MarketingConsultantState) -> Dict[str, Any]:
    """
    Use LLM to perform sophisticated information completeness evaluation.
    
    This goes beyond basic field checking to assess campaign viability,
    information quality, and strategic adequacy.
    
    Args:
        state: Consultation state to evaluate
        
    Returns:
        Dict with LLM evaluation results
    """
    logger.debug("Performing LLM-based completeness evaluation")
    
    try:
        cfg = get_config()
        llm = ChatOpenAI(
            model=cfg.llm_model, 
            temperature=0.1,  # Low temperature for consistent evaluation
            api_key=cfg.openai_api_key
        )
        
        # Create sophisticated evaluation prompt
        system_prompt = _create_evaluation_system_prompt()
        
        # Prepare conversation context
        conversation_context = _prepare_conversation_context(state)
        
        # Get LLM evaluation
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=conversation_context)
        ])
        
        # Parse and validate LLM response
        evaluation_result = _parse_llm_evaluation(response.content)
        
        logger.debug(f"LLM evaluation completed: {evaluation_result.get('has_enough_info')}")
        return evaluation_result
        
    except Exception as e:
        logger.error(f"LLM evaluation failed: {str(e)}")
        raise  # Re-raise to trigger fallback in main function


def _create_evaluation_system_prompt() -> str:
    """
    Create a comprehensive system prompt for LLM evaluation.
    
    This prompt guides the LLM to evaluate information completeness
    from a marketing strategy perspective, not just field filling.
    
    Returns:
        Detailed system prompt for evaluation
    """
    return """
You are an expert marketing strategist evaluating whether we have sufficient information to create an effective marketing campaign.

Evaluation Criteria:
1. GOAL CLARITY: Is the product/service/offering clearly defined and specific enough to create compelling messaging?
2. AUDIENCE SPECIFICITY: Is the target audience defined well enough to create targeted campaigns? Generic terms like "everyone" or "customers" are insufficient.
3. BUDGET ADEQUACY: Is there budget information that allows for strategic planning? Even rough ranges are helpful.
4. CHANNEL APPROPRIATENESS: Are there channel preferences or constraints that guide platform selection?
5. CAMPAIGN VIABILITY: Can we create an effective campaign that has a reasonable chance of success?

Quality Standards:
- Goal should be more specific than "business", "idea", or "product"
- Audience should include demographic, psychographic, or behavioral indicators
- Budget should provide some constraint guidance (even "under $500" vs "several thousand")
- Channels can be preferences, existing platforms, or audience-based recommendations

Return ONLY a valid JSON object with this exact structure:
{
    "has_enough_info": boolean,
    "missing_critical_info": ["specific_field1", "specific_field2"],
    "quality_assessment": {
        "goal_clarity": 0.0-1.0,
        "audience_specificity": 0.0-1.0,
        "budget_adequacy": 0.0-1.0,
        "channel_appropriateness": 0.0-1.0,
        "overall_viability": 0.0-1.0
    },
    "reasoning": "brief explanation of decision",
    "recommendations": ["specific suggestion1", "specific suggestion2"],
    "confidence_score": 0.0-1.0
}

Be strict but realistic. A campaign needs enough specificity to be effective, but perfect information isn't required.
"""


def _prepare_conversation_context(state: MarketingConsultantState) -> str:
    """
    Prepare conversation context for LLM evaluation.
    
    This formats the consultation history and gathered information
    in a way that's easy for the LLM to analyze and evaluate.
    
    Args:
        state: Consultation state with conversation history
        
    Returns:
        Formatted context string for LLM evaluation
    """
    context_lines = [
        "MARKETING CONSULTATION EVALUATION",
        "=" * 40,
        "",
        f"Original User Request: '{state.user_input}'",
        f"Questions Asked: {state.question_count}",
        f"Current Stage: {state.stage}",
        "",
        "GATHERED INFORMATION:",
        "-" * 20
    ]
    
    # Add parsed intent information
    for key, value in state.parsed_intent.items():
        if value:
            formatted_key = key.replace("_", " ").title()
            context_lines.append(f"{formatted_key}: {value}")
        else:
            formatted_key = key.replace("_", " ").title()
            context_lines.append(f"{formatted_key}: [Not provided]")
    
    context_lines.extend(["", "CONVERSATION HISTORY:", "-" * 20])
    
    # Add conversation history
    for i, qa in enumerate(state.qa_history, 1):
        context_lines.append(f"Q{i}: {qa['question']}")
        if qa.get("answer"):
            context_lines.append(f"A{i}: {qa['answer']}")
        else:
            context_lines.append(f"A{i}: [No response yet]")
        context_lines.append("")
    
    # Add any existing issues or concerns
    if state.errors:
        context_lines.extend(["ISSUES ENCOUNTERED:", "-" * 20])
        for error in state.errors:
            context_lines.append(f"- {error}")
        context_lines.append("")
    
    context_lines.extend([
        "EVALUATION REQUEST:",
        "-" * 20,
        "Please evaluate if this information is sufficient for creating an effective marketing campaign.",
        "Consider campaign viability, message targeting, budget planning, and channel strategy.",
        "Provide specific recommendations for any missing critical information."
    ])
    
    return "\n".join(context_lines)


def _parse_llm_evaluation(response_content: str) -> Dict[str, Any]:
    """
    Parse and validate LLM evaluation response.
    
    This handles various response formats and ensures we get
    a properly structured evaluation result.
    
    Args:
        response_content: Raw LLM response content
        
    Returns:
        Parsed and validated evaluation dictionary
    """
    try:
        # Try direct JSON parsing first
        evaluation = json.loads(response_content.strip())
        
        # Validate required fields
        required_fields = ["has_enough_info", "missing_critical_info", "quality_assessment", "reasoning"]
        for field in required_fields:
            if field not in evaluation:
                raise ValueError(f"Missing required field: {field}")
        
        # Ensure quality assessment has expected structure
        quality = evaluation.get("quality_assessment", {})
        expected_quality_fields = ["goal_clarity", "audience_specificity", "budget_adequacy", "channel_appropriateness"]
        for field in expected_quality_fields:
            if field not in quality:
                quality[field] = 0.5  # Default neutral score
        
        # Ensure confidence score exists
        if "confidence_score" not in evaluation:
            evaluation["confidence_score"] = 0.7  # Default moderate confidence
        
        return evaluation
        
    except json.JSONDecodeError:
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
    
    except Exception as e:
        logger.warning(f"Error parsing LLM evaluation: {str(e)}")
    
    # Fallback: create evaluation from response text analysis
    return _create_fallback_evaluation_from_text(response_content)


def _create_fallback_evaluation_from_text(response_content: str) -> Dict[str, Any]:
    """
    Create evaluation from LLM text when JSON parsing fails.
    
    This analyzes the LLM response text to extract evaluation signals
    even when the structured JSON format wasn't followed properly.
    
    Args:
        response_content: LLM response text to analyze
        
    Returns:
        Best-effort evaluation dictionary
    """
    content_lower = response_content.lower()
    
    # Look for positive/negative indicators
    positive_indicators = ["sufficient", "enough", "adequate", "ready", "complete", "yes"]
    negative_indicators = ["insufficient", "missing", "need more", "not enough", "incomplete", "no"]
    
    positive_count = sum(1 for indicator in positive_indicators if indicator in content_lower)
    negative_count = sum(1 for indicator in negative_indicators if indicator in content_lower)
    
    # Determine overall assessment
    has_enough_info = positive_count > negative_count
    
    # Extract any specific missing information mentioned
    missing_terms = ["budget", "audience", "goal", "product", "channel", "target", "specific"]
    missing_critical_info = [term for term in missing_terms if f"missing {term}" in content_lower or f"need {term}" in content_lower]
    
    return {
        "has_enough_info": has_enough_info,
        "missing_critical_info": missing_critical_info,
        "quality_assessment": {
            "goal_clarity": 0.6,
            "audience_specificity": 0.5,
            "budget_adequacy": 0.4,
            "channel_appropriateness": 0.5,
            "overall_viability": 0.5
        },
        "reasoning": f"Fallback evaluation from text analysis. Positive signals: {positive_count}, Negative signals: {negative_count}",
        "recommendations": ["Clarify any vague information", "Provide more specific details"],
        "confidence_score": 0.3  # Low confidence in fallback evaluation
    }


def _combine_evaluations(
    basic_audit: Dict[str, Any], 
    llm_evaluation: Dict[str, Any], 
    state: MarketingConsultantState
) -> Dict[str, Any]:
    """
    Combine basic audit results with LLM evaluation for final assessment.
    
    This creates a comprehensive evaluation that considers both
    basic requirements and sophisticated strategy assessment.
    
    Args:
        basic_audit: Results from basic information audit
        llm_evaluation: Results from LLM evaluation
        state: Current consultation state
        
    Returns:
        Combined final evaluation
    """
    # Start with LLM evaluation as base
    final_evaluation = llm_evaluation.copy()
    
    # Apply basic audit constraints
    if not basic_audit["meets_minimum_requirements"]:
        final_evaluation["has_enough_info"] = False
        final_evaluation["missing_critical_info"].extend(basic_audit["missing_critical"])
    
    # Merge quality assessments
    basic_quality = basic_audit["quality_scores"]
    llm_quality = llm_evaluation.get("quality_assessment", {})
    
    # Take the minimum of basic and LLM scores (most conservative)
    combined_quality = {}
    for key in llm_quality:
        basic_key = key.replace("_quality", "") + "_quality"
        if basic_key in basic_quality:
            combined_quality[key] = min(llm_quality[key], basic_quality[basic_key])
        else:
            combined_quality[key] = llm_quality[key]
    
    final_evaluation["quality_assessment"] = combined_quality
    
    # Adjust confidence based on agreement between evaluations
    basic_says_sufficient = basic_audit["meets_minimum_requirements"]
    llm_says_sufficient = llm_evaluation["has_enough_info"]
    
    if basic_says_sufficient == llm_says_sufficient:
        # Agreement increases confidence
        final_evaluation["confidence_score"] = min(final_evaluation.get("confidence_score", 0.7) * 1.2, 1.0)
    else:
        # Disagreement decreases confidence
        final_evaluation["confidence_score"] = final_evaluation.get("confidence_score", 0.7) * 0.8
    
    # Add evaluation metadata
    final_evaluation["evaluation_metadata"] = {
        "basic_audit_passed": basic_audit["meets_minimum_requirements"],
        "llm_evaluation_passed": llm_evaluation["has_enough_info"],
        "question_count": state.question_count,
        "conversation_engagement": basic_audit.get("average_response_length", 0)
    }
    
    return final_evaluation


def _fallback_evaluation(state: MarketingConsultantState, error_message: str) -> Dict[str, Any]:
    """
    Provide fallback evaluation when all sophisticated methods fail.
    
    This uses simple heuristics to make a reasonable assessment
    when LLM evaluation fails or is unavailable.
    
    Args:
        state: Consultation state to evaluate
        error_message: Description of what went wrong
        
    Returns:
        Conservative fallback evaluation
    """
    logger.warning(f"Using fallback evaluation due to: {error_message}")
    
    # Simple heuristic: need at least goal and audience
    has_goal = bool(state.parsed_intent.get("goal", "").strip())
    has_audience = bool(state.parsed_intent.get("audience", "").strip())
    has_budget = bool(state.parsed_intent.get("budget", "").strip())
    
    # Conservative assessment
    has_enough = has_goal and has_audience and (has_budget or state.question_count >= 4)
    
    missing = []
    if not has_goal:
        missing.append("goal")
    if not has_audience:
        missing.append("audience")
    if not has_budget and state.question_count < 4:
        missing.append("budget")
    
    return {
        "has_enough_info": has_enough,
        "missing_critical_info": missing,
        "quality_assessment": {
            "goal_clarity": 0.5 if has_goal else 0.1,
            "audience_specificity": 0.5 if has_audience else 0.1,
            "budget_adequacy": 0.5 if has_budget else 0.2,
            "channel_appropriateness": 0.5,
            "overall_viability": 0.4 if has_enough else 0.2
        },
        "reasoning": f"Fallback heuristic evaluation. Error: {error_message}",
        "recommendations": ["Provide more detailed information for each missing field"],
        "confidence_score": 0.6 if has_enough else 0.4,
        "evaluation_metadata": {
            "evaluation_method": "fallback_heuristic",
            "error_occurred": True,
            "error_message": error_message
        }
    }


def assess_answer_quality(answer: str, question_type: QuestionType) -> Dict[str, Any]:
    """
    Assess the quality and completeness of a specific answer.
    
    This provides granular feedback on individual responses to help
    determine if follow-up questions or clarifications are needed.
    
    Args:
        answer: User's response to evaluate
        question_type: Type of question this answers
        
    Returns:
        Dict with quality assessment and recommendations
    """
    if not answer or not answer.strip():
        return {
            "quality_score": 0.0,
            "is_adequate": False,
            "issues": ["no_response"],
            "recommendations": ["Please provide a response to the question"]
        }
    
    answer_clean = answer.strip()
    issues = []
    recommendations = []
    quality_score = 0.5  # Start with neutral score
    
    # Length-based assessment
    if len(answer_clean) < 3:
        issues.append("too_brief")
        recommendations.append("Please provide more details")
        quality_score *= 0.3
    elif len(answer_clean) > 50:
        quality_score *= 1.2  # Bonus for detailed responses
    
    # Question-type specific assessment
    if question_type == QuestionType.PRODUCT_SERVICE:
        generic_terms = ["business", "idea", "product", "service", "thing"]
        if any(term in answer_clean.lower() for term in generic_terms):
            issues.append("too_generic")
            recommendations.append("Please be more specific about what you're promoting")
            quality_score *= 0.4
    
    elif question_type == QuestionType.TARGET_AUDIENCE:
        generic_audiences = ["people", "everyone", "customers", "users", "public"]
        if any(term in answer_clean.lower() for term in generic_audiences):
            issues.append("audience_too_broad")
            recommendations.append("Please specify a more targeted audience (age, profession, interests)")
            quality_score *= 0.3
    
    elif question_type == QuestionType.BUDGET:
        # Look for any numeric indicators or range terms
        has_numbers = bool(re.search(r'\d', answer_clean))
        budget_terms = ["under", "over", "around", "approximately", "budget", "$", "thousand", "hundred"]
        has_budget_context = any(term in answer_clean.lower() for term in budget_terms)
        
        if not (has_numbers or has_budget_context):
            issues.append("no_budget_indication")
            recommendations.append("Please provide a budget range or amount")
            quality_score *= 0.2
    
    # Final quality assessment
    quality_score = min(quality_score, 1.0)
    is_adequate = quality_score >= 0.6 and len(issues) <= 1
    
    return {
        "quality_score": quality_score,
        "is_adequate": is_adequate,
        "issues": issues,
        "recommendations": recommendations,
        "answer_length": len(answer_clean),
        "specificity_indicators": _count_specificity_indicators(answer_clean)
    }


def _count_specificity_indicators(text: str) -> int:
    """
    Count indicators of response specificity and detail.
    
    Args:
        text: Response text to analyze
        
    Returns:
        Number of specificity indicators found
    """
    specificity_patterns = [
        r'\d+',  # Numbers
        r'\b(?:aged?|between|from|to)\s+\d+',  # Age ranges
        r'\b(?:professionals?|students?|seniors?|millennials?)',  # Demographic terms
        r'\b(?:local|online|mobile|social)',  # Context specifiers
        r'\$\d+',  # Dollar amounts
        r'\b(?:instagram|facebook|twitter|linkedin|email)',  # Specific platforms
        r'\b(?:daily|weekly|monthly|annually)',  # Time specificity
    ]
    
    count = 0
    for pattern in specificity_patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    
    return count
