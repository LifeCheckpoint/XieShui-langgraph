"""
Deep Research Graph - 重构版本
使用新的节点实现和服务抽象层
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from src.deep_research.utils.state import MainAgentState
from src.deep_research.nodes_v2.planning import plan_research, generate_search_queries
from src.deep_research.nodes_v2.searching import execute_search, filter_search_results
from src.deep_research.nodes_v2.reading import read_and_summarize
from src.deep_research.nodes_v2.routing import initialize_research, update_and_check_cycle
from src.deep_research.nodes_v2.writing import generate_outline, write_sections, finetune_report


def create_research_graph() -> StateGraph:
    # 创建状态图
    builder = StateGraph(MainAgentState)
    
    # 添加所有节点
    builder.add_node("initialize_research", initialize_research)
    builder.add_node("plan_research", plan_research)
    builder.add_node("generate_search_queries", generate_search_queries)
    builder.add_node("execute_search", execute_search)
    builder.add_node("filter_search_results", filter_search_results)
    builder.add_node("read_and_summarize", read_and_summarize)
    builder.add_node("generate_outline", generate_outline)
    builder.add_node("write_sections", write_sections)
    builder.add_node("finetune_report", finetune_report)
    
    # 添加边（保持完全相同的流程）
    builder.add_edge(START, "initialize_research")
    builder.add_edge("initialize_research", "plan_research")
    builder.add_edge("plan_research", "generate_search_queries")
    builder.add_edge("generate_search_queries", "execute_search")
    builder.add_edge("execute_search", "filter_search_results")
    builder.add_edge("filter_search_results", "read_and_summarize")
    
    # 添加条件边用于循环控制
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
    
    return builder


def create_research_graph_with_checkpointer():
    """创建带有检查点的研究图"""
    builder = create_research_graph()
    return builder.compile(checkpointer=True)


def create_simple_research_graph():
    """创建简单的研究图（不带检查点）"""
    builder = create_research_graph()
    return builder.compile()


# 为了向后兼容，保留原有的builder导出
builder = create_research_graph()
graph = builder.compile(checkpointer=True)

__all__ = ["builder", "graph", "create_research_graph", "create_research_graph_with_checkpointer"]
