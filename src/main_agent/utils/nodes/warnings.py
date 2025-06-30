from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import ToolMessage
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState


def no_tools_warning(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    工具未调用警告节点，提示 Agent 没有调用工具
    """
    return {"messages": [ToolMessage(
        content="目前没有调用任何工具，请检查你需要调用什么工具。如果你认为当前任务已经结束，则使用 `attempt_completion` 工具向系统确认该次任务完成",
        tool_call_id="internal_warning"
    )]}