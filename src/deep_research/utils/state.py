"""
榭水 Deep Research Agent 状态管理
"""

from __future__ import annotations

from typing import TypedDict, Annotated, List
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class ResearchCycleState(TypedDict):
    """单个研究循环的状态"""
    cycle_count: int
    research_plan: dict
    search_queries: List[str]
    search_results: List[dict]
    reading_list: List[str]
    findings: List[str]

class MainAgentState(TypedDict):
    """深度研究代理状态模型"""
    messages: Annotated[List[AnyMessage], add_messages]
    topic: str
    research_summary: str
    research_cycles: List[ResearchCycleState]
    report: str

__all__ = ["MainAgentState", "ResearchCycleState"]