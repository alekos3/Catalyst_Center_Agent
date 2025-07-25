#!/usr/bin/env python3
__author__ = "Alexios Nersessian"
__copyright__ = "Copyright 2025, Alexios Nersessian"
__version__ = "v1"

from ai_tools import get_auth_token, get_device_inventory, get_device_config
import streamlit as st
from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

import os
import urllib3

urllib3.disable_warnings()

# Retrieve AI API key
OPENAI_API_KEY = os.getenv("AI_ACCESS_TOKEN")

if not OPENAI_API_KEY:
    raise EnvironmentError("OpenAI API key is missing. Please check your .env file or environment variables.")


class State(TypedDict):
    messages: Annotated[list, add_messages]


# ---- Graph & LLM Setup ----
def setup_langgraph_tools() -> List:
    """Returns a list of tool functions for LangGraph."""
    return [get_auth_token, get_device_inventory, get_device_config]


def setup_llm_with_tools(tools: List, model: str) -> Any:
    """Initializes and returns LLM bound with tools."""
    llm = ChatOpenAI(
        model=model,
        api_key=OPENAI_API_KEY
    )
    return llm.bind_tools(tools)


def build_langgraph(tools: List, llm_with_tools: Any) -> Any:
    """Compiles and returns the LangGraph."""
    graph_builder = StateGraph(State)

    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph_builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_conditional_edges("chatbot", tools_condition,)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)


# ---- Streamlit UI Logic ----
def initialize_session_state():
    """Ensures 'messages' exists in session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def get_user_input() -> str:
    """Displays input box and returns user input."""
    return st.text_input("You:", placeholder="Type your question here...")


def process_user_message(user_input: str, graph: Any, config: Dict) -> None:
    """Processes user message, updates chat history and displays response."""
    state = {"messages": st.session_state.messages}
    state["messages"].append({"role": "user", "content": user_input})
    events = graph.stream(state, config, stream_mode="values")
    final_response = None
    for event in events:
        if "messages" in event:
            assistant_message = event["messages"][-1]
            print("THINKING:", assistant_message)
            try:
                if isinstance(assistant_message, dict):
                    final_response = assistant_message.get("content", "No content available")
                else:
                    final_response = getattr(assistant_message, "content", "No content available")
            except Exception as e:
                print(f"Error processing assistant message: {e}")
                final_response = "Error displaying response."
    if final_response:
        st.session_state.messages.append({"role": "assistant", "content": final_response})


def display_chat_history():
    """Renders the chat history in the UI."""
    st.write("### Chat History")
    for msg in st.session_state.messages:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                st.write(f"**You:** {msg['content']}")
            elif msg.get("role") == "assistant":
                st.write(f"**Assistant:** {msg['content']}")


# ---- Main Routine ----
def main():
    st.title("Catalyst Center Agent Buddy")
    initialize_session_state()
    tools = setup_langgraph_tools()
    llm_with_tools = setup_llm_with_tools(tools, "gpt-4.1")
    graph = build_langgraph(tools, llm_with_tools)
    config = {"configurable": {"thread_id": "1"}}
    user_input = get_user_input()

    if st.button("Send") and user_input.strip():
        process_user_message(user_input, graph, config)
    display_chat_history()


if __name__ == "__main__":
    main()
