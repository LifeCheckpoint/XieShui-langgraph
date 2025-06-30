"""
Main Agent 的节点定义

Agent 将在这些节点之间进行切换，处理任务
"""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from typing import Any, Dict

from conf import Configuration
from state import MainAgentState


async def welcome(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    欢迎节点，在该节点中注入系统提示词与欢迎信息
    """
    

__all__ = ["welcome"]