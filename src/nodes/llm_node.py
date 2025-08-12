from typing import Dict
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langsmith import traceable
from src.utils.state import MessagesState
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set!")

VERBOSE_LLM = os.getenv("VERBOSE_LLM", "false").strip().lower() in {"1", "true", "on"}
if VERBOSE_LLM:
    print("Initializing ChatOpenAI with API key:", api_key[:6] + "..." if api_key else "None")

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    api_key=api_key
)

@traceable(name = "LLM Node")

def llm_node(state: MessagesState) -> MessagesState:
    """Process messages and generate a response using the LLM."""
    
    messages = state["messages"]
    
    # Add system message only if it's not present
    if not messages or not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [
            SystemMessage(content="You are a helpful AI assistant.")
        ] + messages
    
    try:
        if VERBOSE_LLM:
            print("\nSending messages to LLM:", [f"{msg.__class__.__name__}: {msg.content[:50]}..." for msg in messages])
        # Generate response
        response = llm.invoke(messages)
        if VERBOSE_LLM:
            print("Received response from LLM:", response.content[:100] + "...")
        
        # Return new state with response
        return {"messages": messages + [AIMessage(content=response.content)]}
        
    except Exception as e:
        if VERBOSE_LLM:
            print("\nError in LLM Node:")
            print("Type:", type(e).__name__)
            print("Message:", str(e))
            print("Messages state:", messages)
        raise  # Re-raise the exception to see the full traceback