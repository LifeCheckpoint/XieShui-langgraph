"""
榭水 Deep Research Agent 状态管理
"""

from __future__ import annotations

from typing import Annotated, List, Any
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class MainAgentState(BaseModel):
    """
    Agent 状态模型
    """
    messages: Annotated[List[AnyMessage], add_messages] = Field(default=[], description="Agent 消息列表，包含交互历史，储存和传递对话内容")
    current_user_info: dict = Field(default={}, description="当前用户信息，包含用户的基本信息和偏好设置")
    previous_info: List[Any] = Field(default=None, description="先前信息的精简总结，用于指导 Agent 决策")
    agent_mode: str = Field(default="default", description="Agent 模式，指示当前深度研究所处的阶段", examples=["default", "research", "execution"])

__all__ = ["MainAgentState"]