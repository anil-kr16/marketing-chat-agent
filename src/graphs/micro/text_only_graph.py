"""
Text-only micro graph for focused text generation testing.

This graph focuses solely on text generation workflow:
User Input → Parse Intent → Generate Text → Output
"""

from __future__ import annotations
from langgraph.graph import StateGraph, END
from src.utils.state import MessagesState
from src.nodes.intent.parse_intent_node import parse_intent_node
from src.nodes.generation.text.text_generation_node import text_generation_node
from langchain.schema import SystemMessage, AIMessage


def create_text_only_graph() -> StateGraph:
    """
    Create a focused text generation graph.
    
    This micro graph is designed for:
    - Unit testing text generation
    - Isolated text content development  
    - Performance testing of text generation
    - Debugging text generation issues
    
    Flow:
    START → parse_intent → text_generation → END
    """
    
    def add_system_message(state: MessagesState) -> MessagesState:
        """Add system message if not present."""
        messages = state.get("messages", [])
        has_system = any(isinstance(msg, SystemMessage) for msg in messages)
        
        if not has_system:
            system_msg = SystemMessage(
                content="You are a specialized text generation agent focused on creating high-quality marketing content."
            )
            messages = [system_msg] + messages
            state = {**state, "messages": messages}
        
        return state
    
    def finalize_text_output(state: MessagesState) -> MessagesState:
        """Create final AI response with generated text."""
        post_content = state.get("post_content", "")
        parsed_intent = state.get("parsed_intent", {})
        
        if post_content:
            goal = parsed_intent.get("goal", "campaign")
            channels = parsed_intent.get("channels", ["Email"])
            
            response_content = f"""✅ TEXT GENERATED SUCCESSFULLY!

📝 Generated Content:
{post_content}

🎯 Campaign Goal: {goal}
📱 Target Channels: {', '.join(channels)}

🔍 Intent Details:
- Audience: {parsed_intent.get('audience', 'General')}
- Tone: {parsed_intent.get('tone', 'Professional')}
- Budget: {parsed_intent.get('budget', 'Not specified')}"""
        else:
            response_content = "❌ Text generation failed. Please try again with a clearer prompt."
        
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
    graph.add_node("text_generation", text_generation_node)
    graph.add_node("finalize_output", finalize_text_output)
    
    # Define the flow
    graph.add_edge("system_setup", "parse_intent")
    graph.add_edge("parse_intent", "text_generation")
    graph.add_edge("text_generation", "finalize_output")
    graph.add_edge("finalize_output", END)
    
    # Set entry point
    graph.set_entry_point("system_setup")
    
    return graph


def get_text_only_graph():
    """Get the compiled text-only graph."""
    graph = create_text_only_graph()
    return graph.compile()
