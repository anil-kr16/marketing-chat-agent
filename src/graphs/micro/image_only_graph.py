"""
Image-only micro graph for focused image generation testing.

This graph focuses solely on image generation workflow:
User Input → Parse Intent → Generate Image → Output
"""

from __future__ import annotations
from langgraph.graph import StateGraph, END
from src.utils.state import MessagesState
from src.nodes.intent.parse_intent_node import parse_intent_node
from src.nodes.generation.image.image_generation_node import image_generation_node
from langchain.schema import SystemMessage, AIMessage
import os


def create_image_only_graph() -> StateGraph:
    """
    Create a focused image generation graph.
    
    This micro graph is designed for:
    - Unit testing image generation
    - Isolated image creation development
    - Performance testing of image generation
    - Debugging DALL-E integration issues
    
    Flow:
    START → parse_intent → image_generation → END
    """
    
    def add_system_message(state: MessagesState) -> MessagesState:
        """Add system message if not present."""
        messages = state.get("messages", [])
        has_system = any(isinstance(msg, SystemMessage) for msg in messages)
        
        if not has_system:
            system_msg = SystemMessage(
                content="You are a specialized image generation agent focused on creating compelling visual content for marketing campaigns."
            )
            messages = [system_msg] + messages
            state = {**state, "messages": messages}
        
        return state
    
    def finalize_image_output(state: MessagesState) -> MessagesState:
        """Create final AI response with generated image details."""
        image_url = state.get("image_url", "")
        image_prompt = state.get("image_prompt", "")
        parsed_intent = state.get("parsed_intent", {})
        
        if image_url:
            goal = parsed_intent.get("goal", "campaign")
            
            # Check if file actually exists
            file_exists = False
            file_size = "Unknown"
            if image_url.startswith("/static/images/"):
                filename = os.path.basename(image_url)
                file_path = os.path.join("static", "images", filename)
                if os.path.exists(file_path):
                    file_exists = True
                    file_size = f"{os.path.getsize(file_path) / 1024:.1f} KB"
            
            response_content = f"""✅ IMAGE GENERATED SUCCESSFULLY!

🖼️ Image Details:
- URL: {image_url}
- File Size: {file_size}
- File Exists: {'✅ Yes' if file_exists else '❌ No'}

🎨 Generation Prompt:
{image_prompt}

🎯 Campaign Context:
- Goal: {goal}
- Audience: {parsed_intent.get('audience', 'General')}
- Tone: {parsed_intent.get('tone', 'Professional')}

📊 Technical Info:
- Model: DALL-E 3
- Format: PNG
- Resolution: 1024x1024"""
        else:
            response_content = f"""❌ IMAGE GENERATION FAILED!

🔍 Debug Information:
- Image URL: {image_url}
- Image Prompt: {image_prompt}
- Intent Parsed: {'✅' if parsed_intent else '❌'}

💡 Troubleshooting:
- Check OpenAI API key is set
- Verify DALL-E 3 access
- Review prompt for policy violations
- Check network connectivity"""
        
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
    graph.add_node("image_generation", image_generation_node)
    graph.add_node("finalize_output", finalize_image_output)
    
    # Define the flow
    graph.add_edge("system_setup", "parse_intent")
    graph.add_edge("parse_intent", "image_generation")
    graph.add_edge("image_generation", "finalize_output")
    graph.add_edge("finalize_output", END)
    
    # Set entry point
    graph.set_entry_point("system_setup")
    
    return graph


def get_image_only_graph():
    """Get the compiled image-only graph."""
    graph = create_image_only_graph()
    return graph.compile()
