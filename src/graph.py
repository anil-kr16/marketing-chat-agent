from langgraph.graph import StateGraph, START, END
from src.nodes.llm_node import llm_node
from src.utils.state import MessagesState, init_state
from src.utils.logger import enable_langsmith

enable_langsmith()

def visualize_graph(graph):
    """Create and display a visualization of the graph."""
    try:
        from IPython.display import Image, display
        from langgraph.graph import END, START
        
        # Create Mermaid diagram
        return display(Image(graph.get_graph().draw_mermaid_png()))
        
    except ImportError:
        print("Note: Install IPython to see graph visualization")
    except Exception as e:
        print(f"Note: Could not create graph visualization: {str(e)}")

def build_graph(): 
    """Build and return the state graph."""
    # Create graph with state type
    builder = StateGraph(MessagesState)
    
    # Add nodes
    builder.add_node("llm", llm_node)
    
    # Add edges
    builder.add_edge(START, "llm")
    builder.add_edge("llm", END)
    
    # Compile
    graph = builder.compile()
    
    return graph

# Expose the graph for LangGraph Dev or CLI
graph = build_graph()