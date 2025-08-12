from __future__ import annotations

from langsmith import traceable
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from src.agents.core.base_agent import BaseAgent
from src.utils.state import MessagesState
from src.nodes.intent.parse_intent_node import parse_intent_node
from src.nodes.generation.text.text_generation_node import text_generation_node


class TextOnlyAgent(BaseAgent):
    """
    Micro agent focused solely on text generation.
    
    Simple linear workflow: Parse Intent → Generate Text
    Perfect for unit testing text generation in isolation.
    """

    @traceable(name="Text Only Agent")
    def run(self, state: MessagesState) -> MessagesState:
        """Run text generation workflow."""
        # Ensure system message exists
        messages = state.get("messages", [])
        has_system = any(isinstance(msg, SystemMessage) for msg in messages)
        
        if not has_system:
            system_msg = SystemMessage(
                content="You are a specialized text generation agent focused on creating high-quality marketing content."
            )
            messages = [system_msg] + messages
            state = {**state, "messages": messages}
        
        # Parse intent for text generation context
        state = parse_intent_node(state)
        
        # Generate marketing text
        state = text_generation_node(state)
        
        # Create completion message
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
            response_content = "❌ Text generation failed. Please check your configuration."
        
        # Add AI response
        messages = state.get("messages", [])
        messages.append(AIMessage(content=response_content))
        
        return {
            **state,  # Preserve all state including post_content
            "messages": messages
        }
