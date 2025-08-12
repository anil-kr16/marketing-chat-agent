from typing import TypedDict, Annotated, Optional, Dict, List, Any
from langchain.schema import BaseMessage
from langgraph.graph.message import add_messages

class MessagesState(TypedDict, total=False):
    """Type definition for marketing chat state with all workflow fields."""
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Core content fields
    post_content: Optional[str]
    hashtags: Optional[List[str]]
    ctas: Optional[List[str]]
    image_url: Optional[str]
    image_prompt: Optional[str]
    
    # Intent and planning
    parsed_intent: Optional[Dict[str, Any]]
    creative_brief: Optional[str]
    
    # Response composition
    final_response: Optional[Dict[str, Any]]
    
    # Delivery tracking
    delivery: Optional[Dict[str, Any]]
    
    # Metadata
    meta: Optional[Dict[str, Any]]
    llmMetadata: Optional[Dict[str, Any]]

def init_state() -> MessagesState:
    """Initialize the state for the chat agent."""
    return {
        "messages": []
    }