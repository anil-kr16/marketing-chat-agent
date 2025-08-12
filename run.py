"""
CLI entrypoint for running the chat agent.
"""
import os
import time
from dotenv import load_dotenv
from langchain.schema import HumanMessage, AIMessage, SystemMessage

def print_colored(text, color_code):
    """Print text in color"""
    print(f"\033[{color_code}m{text}\033[0m")

def print_typing_effect(text, delay=0.03):
    """Print text with a typing effect"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def print_banner():
    """Print a beautiful banner"""
    print("\n" + "="*50)
    print_colored("🤖 AI Chat Assistant", "36")
    print_colored("Type 'quit' or press Ctrl+C to exit", "33")
    print("="*50 + "\n")

# Load environment variables
load_dotenv()

# Debug: Check if environment variables are loaded (in gray)
print_colored("OPENAI_API_KEY present: " + str(bool(os.getenv("OPENAI_API_KEY"))), "90")

from src.graph import build_graph
from src.utils.state import init_state
from src.utils.logger import enable_langsmith

# Enable LangSmith tracing
enable_langsmith()

# Build the LangGraph
graph = build_graph()

# Create initial state
state = init_state()

# Print welcome banner
print_banner()

def format_message(role, message, typing=False):
    """Format and print a chat message with appropriate styling"""
    if role == "user":
        print_colored("\n👤 You:", "32")  # Green
    else:
        print_colored("\n🤖 Assistant:", "36")  # Cyan
    
    if typing:
        print_typing_effect(message)
    else:
        print(message)
    print()  # Add spacing between messages

# Main chat loop
while True:
    try:
        # Get user input with colored prompt
        user_input = input("\033[32m👤 You:\033[0m ")
        if user_input.lower() in {"exit", "quit", "bye", "goodbye"}:
            print_colored("\n👋 Goodbye! Have a great day!", "33")
            break

        if not user_input.strip():
            continue

        # Create message state
        messages_state = {"messages": [HumanMessage(content=user_input)]}
        
        # Run graph
        result = graph.invoke(messages_state)
        
        # Update state and print messages
        if result and result["messages"]:
            state = result
            # Print only the last AI message
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    print_colored("\n🤖 Assistant:", "36")
                    print_typing_effect(msg.content)
                    print()  # Add spacing
                    break
    except KeyboardInterrupt:
        print_colored("\n\n👋 Goodbye! Have a great day!", "33")
        break
    except Exception as e:
        print_colored(f"\n❌ Error: {str(e)}", "31")  # Red error message
        print_colored("Please try again or type 'quit' to exit.", "33")