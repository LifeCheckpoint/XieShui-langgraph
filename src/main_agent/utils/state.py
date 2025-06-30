"""
榭水主 Agent 状态管理
"""

from __future__ import annotations

from pydantic import BaseModel, Field

class MainAgentState(BaseModel):
    """
    Agent 状态模型
    """
    current_user_info: dict = Field(description="当前用户信息，包含用户的基本信息和偏好设置")
    agent_mode: str = Field(description="Agent 模式，指示当前的工作模式或任务类型", examples=["ddefault", "research", "execution"])

__all__ = ["MainAgentState"]