from __future__ import annotations

import os
from langsmith import traceable
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from src.agents.core.base_agent import BaseAgent
from src.utils.state import MessagesState
from src.nodes.intent.parse_intent_node import parse_intent_node
from src.nodes.generation.image.image_generation_node import image_generation_node


class ImageOnlyAgent(BaseAgent):
    """
    Micro agent focused solely on image generation.
    
    Simple linear workflow: Parse Intent → Generate Image
    Perfect for unit testing image generation in isolation.
    """

    @traceable(name="Image Only Agent")
    def run(self, state: MessagesState) -> MessagesState:
        """Run image generation workflow."""
        # Ensure system message exists
        messages = state.get("messages", [])
        has_system = any(isinstance(msg, SystemMessage) for msg in messages)
        
        if not has_system:
            system_msg = SystemMessage(
                content="You are a specialized image generation agent focused on creating compelling visual content for marketing campaigns."
            )
            messages = [system_msg] + messages
            state = {**state, "messages": messages}
        
        # Parse intent for image generation context
        state = parse_intent_node(state)
        
        # Generate marketing image
        state = image_generation_node(state)
        
        # Create completion message
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
- Tone: {parsed_intent.get('tone', 'Professional')}"""
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
        
        # Add AI response
        messages = state.get("messages", [])
        messages.append(AIMessage(content=response_content))
        
        return {
            **state,  # Preserve all state including image_url, image_prompt
            "messages": messages
        }