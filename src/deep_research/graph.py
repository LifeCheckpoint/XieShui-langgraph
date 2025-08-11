from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from src.deep_research.utils.state import MainAgentState
# 重构后：使用新的nodes_v2实现，确保向后兼容
from src.deep_research.nodes_v2.planning import plan_research, generate_search_queries
from src.deep_research.nodes_v2.searching import execute_search, filter_search_results
from src.deep_research.nodes_v2.reading import read_and_summarize
from src.deep_research.nodes_v2.routing import initialize_research, update_and_check_cycle
from src.deep_research.nodes_v2.writing import generate_outline, write_sections, finetune_report

# --- Build Graph ---

builder = StateGraph(MainAgentState)

# Add nodes
builder.add_node("initialize_research", initialize_research)
builder.add_node("plan_research", plan_research)
builder.add_node("generate_search_queries", generate_search_queries)
builder.add_node("execute_search", execute_search)
builder.add_node("filter_search_results", filter_search_results)
builder.add_node("read_and_summarize", read_and_summarize)
builder.add_node("generate_outline", generate_outline)
builder.add_node("write_sections", write_sections)
builder.add_node("finetune_report", finetune_report)

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
        "generate_report": "generate_outline"
    }
)

builder.add_edge("generate_outline", "write_sections")
builder.add_edge("write_sections", "finetune_report")
builder.add_edge("finetune_report", END)

# Compile the graph
graph = builder.compile(checkpointer=True)

__all__ = ["graph"]