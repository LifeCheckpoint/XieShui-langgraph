from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from aiopath import AsyncPath
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState


async def welcome(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    欢迎节点，在该节点中注入系统提示词与欢迎信息
    """
    # 读取提示词
    system_prompt_path: AsyncPath = AsyncPath(__file__).parent.parent / "instruction.txt"
    system_prompt: str = (await system_prompt_path.read_text(encoding="utf-8")).strip()

    # 替换模板
    system_prompt = system_prompt.replace("<<user_instruction>>", config.get("configurable", {}).get("extra_system_prompt", ""))

    # 注入系统提示词
    return {"messages": [SystemMessage(content=system_prompt)]}