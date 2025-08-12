"""
Hashtag-only micro graph for focused hashtag and CTA generation testing.

This graph focuses solely on hashtag/CTA generation workflow:
User Input → Parse Intent → Generate Hashtags/CTAs → Output
"""

from __future__ import annotations
from langgraph.graph import StateGraph, END
from src.utils.state import MessagesState
from src.nodes.intent.parse_intent_node import parse_intent_node
from src.nodes.generation.cta_hashtag.cta_hashtag_node import cta_hashtag_node
from langchain.schema import SystemMessage, AIMessage


def create_hashtag_only_graph() -> StateGraph:
    """
    Create a focused hashtag and CTA generation graph.
    
    This micro graph is designed for:
    - Unit testing hashtag generation
    - Isolated CTA creation development
    - Performance testing of hashtag generation
    - Debugging hashtag/CTA quality issues
    
    Flow:
    START → parse_intent → hashtag_generation → END
    """
    
    def add_system_message(state: MessagesState) -> MessagesState:
        """Add system message if not present."""
        messages = state.get("messages", [])
        has_system = any(isinstance(msg, SystemMessage) for msg in messages)
        
        if not has_system:
            system_msg = SystemMessage(
                content="You are a specialized hashtag and call-to-action generation agent focused on creating engaging social media elements."
            )
            messages = [system_msg] + messages
            state = {**state, "messages": messages}
        
        return state
    
    def finalize_hashtag_output(state: MessagesState) -> MessagesState:
        """Create final AI response with generated hashtags and CTAs."""
        hashtags = state.get("hashtags", [])
        ctas = state.get("ctas", [])
        parsed_intent = state.get("parsed_intent", {})
        
        if hashtags or ctas:
            goal = parsed_intent.get("goal", "campaign")
            channels = parsed_intent.get("channels", ["Social Media"])
            
            # Format hashtags
            hashtag_display = ""
            if hashtags:
                hashtag_display = "\n".join(f"  • {tag}" for tag in hashtags)
            else:
                hashtag_display = "  (No hashtags generated)"
            
            # Format CTAs
            cta_display = ""
            if ctas:
                cta_display = "\n".join(f"  • {cta}" for cta in ctas)
            else:
                cta_display = "  (No CTAs generated)"
            
            # Generate statistics
            hashtag_count = len(hashtags)
            cta_count = len(ctas)
            valid_hashtags = sum(1 for tag in hashtags if tag.startswith("#")) if hashtags else 0
            
            response_content = f"""✅ HASHTAGS & CTAS GENERATED SUCCESSFULLY!

🏷️ Hashtags ({hashtag_count} total):
{hashtag_display}

📢 Call-to-Actions ({cta_count} total):
{cta_display}

🎯 Campaign Context:
- Goal: {goal}
- Channels: {', '.join(channels)}
- Audience: {parsed_intent.get('audience', 'General')}
- Tone: {parsed_intent.get('tone', 'Professional')}

📊 Quality Metrics:
- Valid Hashtags: {valid_hashtags}/{hashtag_count} ({'✅' if valid_hashtags == hashtag_count else '⚠️'})
- Hashtag Length: {f'Avg {sum(len(tag) for tag in hashtags) / len(hashtags):.1f} chars' if hashtags else 'N/A'}
- CTA Variety: {'✅ Good' if cta_count >= 2 else '⚠️ Limited' if cta_count == 1 else '❌ None'}"""
        else:
            response_content = f"""❌ HASHTAG/CTA GENERATION FAILED!

🔍 Debug Information:
- Hashtags Generated: {len(hashtags)}
- CTAs Generated: {len(ctas)}
- Intent Parsed: {'✅' if parsed_intent else '❌'}
- Goal: {parsed_intent.get('goal', 'Not detected')}

💡 Troubleshooting:
- Check OpenAI API key is set
- Verify prompt clarity
- Review input for specific products/services
- Ensure goal is well-defined"""
        
        # Add AI response while preserving all state
        messages = state.get("messages", [])
        messages.append(AIMessage(content=response_content))
        
        # Return complete state with all keys preserved
        return {
            **state,  # Preserve all existing state
            "messages": messages
        }
    
    # Create the graph
    graph = StateGraph(MessagesState)
    
    # Add nodes
    graph.add_node("system_setup", add_system_message)
    graph.add_node("parse_intent", parse_intent_node)
    graph.add_node("hashtag_generation", cta_hashtag_node)
    graph.add_node("finalize_output", finalize_hashtag_output)
    
    # Define the flow
    graph.add_edge("system_setup", "parse_intent")
    graph.add_edge("parse_intent", "hashtag_generation")
    graph.add_edge("hashtag_generation", "finalize_output")
    graph.add_edge("finalize_output", END)
    
    # Set entry point
    graph.set_entry_point("system_setup")
    
    return graph


def get_hashtag_only_graph():
    """Get the compiled hashtag-only graph."""
    graph = create_hashtag_only_graph()
    return graph.compile()
