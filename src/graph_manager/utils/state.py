"""
知识图谱 Agent 状态管理
"""

from __future__ import annotations

from typing import Annotated, List
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class MainAgentState(BaseModel):
    """
    Agent 状态模型
    """
    messages: Annotated[List[AnyMessage], add_messages] = Field(default=[], description="Agent 消息列表，包含交互历史，储存和传递对话内容")
    task_book: str = Field(description="任务书，由管理者进行填充")

__all__ = ["MainAgentState"]