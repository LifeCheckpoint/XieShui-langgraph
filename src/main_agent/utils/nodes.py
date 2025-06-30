"""
Main Agent 的节点定义

Agent 将在这些节点之间进行切换，处理任务
"""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage
from pathlib import Path
from typing import Any, Dict

from state import MainAgentState


async def welcome(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    欢迎节点，在该节点中注入系统提示词与欢迎信息
    """
    # 读取提示词
    system_prompt_path = Path(__file__).parent / "instruction.txt"
    
    if not system_prompt_path.exists():
        # TODO error node
        pass

    try:
        system_prompt = system_prompt_path.read_text(encoding="utf-8")

        # 替换模板
        system_prompt = system_prompt.format_map({
            "user_instruction": config.get("configurable", {}).extra_system_prompt,
        })

    except Exception as e:
        # TODO error node
        pass

    # 注入系统提示词
    return {"messages": [SystemMessage(content=system_prompt)]}

__all__ = ["welcome"]