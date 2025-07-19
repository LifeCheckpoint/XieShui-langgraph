from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.deep_research.utils.state import MainAgentState
from src.deep_research.nodes.planning import plan_research, generate_search_queries
from src.deep_research.nodes.searching import execute_search, filter_search_results
from src.deep_research.nodes.reading import read_and_summarize
from src.deep_research.nodes.routing import initialize_research, update_and_check_cycle

# --- Build Graph ---

builder = StateGraph(MainAgentState)

# Add nodes
builder.add_node("initialize_research", initialize_research)
builder.add_node("plan_research", plan_research)
builder.add_node("generate_search_queries", generate_search_queries)
builder.add_node("execute_search", execute_search)
builder.add_node("filter_search_results", filter_search_results)
builder.add_node("read_and_summarize", read_and_summarize)
# Note: generate_report node will be added by the user

# Add edges
builder.add_edge(START, "initialize_research")
builder.add_edge("initialize_research", "plan_research")
builder.add_edge("plan_research", "generate_search_queries")
builder.add_edge("generate_search_queries", "execute_search")
builder.add_edge("execute_search", "filter_search_results")
builder.add_edge("filter_search_results", "read_and_summarize")

# Add conditional edge for cycling
builder.add_conditional_edges(
    "read_and_summarize",
    update_and_check_cycle,
    {
        "plan_research": "plan_research",
        "generate_report": END # Temporarily end here, user will add generate_report node
    }
)

# Compile the graph
graph = builder.compile(checkpointer=MemorySaver())

__all__ = ["graph"]