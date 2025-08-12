import os

from dotenv import load_dotenv

def enable_langsmith(project_name: str = "langgraph-chat-agent"):
    """
    This function enables LangSmith logging by setting the necessary environment variables.

    Langsmith is a platform that allows you to log and analyze your LangGraph runs.
    It is a paid service, but you can get a free account by signing up for a free trial.
    """
    
    load_dotenv();
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = project_name
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")

    print("LangSmith logging enabled")

   