from __future__ import annotations

from langsmith import traceable
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from src.agents.core.base_agent import BaseAgent
from src.utils.state import MessagesState
from src.nodes.intent.parse_intent_node import parse_intent_node
from src.nodes.generation.cta_hashtag.cta_hashtag_node import cta_hashtag_node


class HashtagOnlyAgent(BaseAgent):
    """
    Micro agent focused solely on hashtag and CTA generation.
    
    Simple linear workflow: Parse Intent → Generate Hashtags/CTAs
    Perfect for unit testing hashtag generation in isolation.
    """

    @traceable(name="Hashtag Only Agent")
    def run(self, state: MessagesState) -> MessagesState:
        """Run hashtag/CTA generation workflow."""
        # Ensure system message exists
        messages = state.get("messages", [])
        has_system = any(isinstance(msg, SystemMessage) for msg in messages)
        
        if not has_system:
            system_msg = SystemMessage(
                content="You are a specialized hashtag and call-to-action generation agent focused on creating engaging social media elements."
            )
            messages = [system_msg] + messages
            state = {**state, "messages": messages}
        
        # Parse intent for hashtag generation context
        state = parse_intent_node(state)
        
        # Generate hashtags and CTAs
        state = cta_hashtag_node(state)
        
        # Create completion message
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
            
            response_content = f"""✅ HASHTAGS & CTAS GENERATED SUCCESSFULLY!

🏷️ Hashtags ({len(hashtags)} total):
{hashtag_display}

📢 Call-to-Actions ({len(ctas)} total):
{cta_display}

🎯 Campaign Context:
- Goal: {goal}
- Channels: {', '.join(channels)}
- Audience: {parsed_intent.get('audience', 'General')}
- Tone: {parsed_intent.get('tone', 'Professional')}"""
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
        
        # Add AI response
        messages = state.get("messages", [])
        messages.append(AIMessage(content=response_content))
        
        return {
            **state,  # Preserve all state including hashtags, ctas
            "messages": messages
        }