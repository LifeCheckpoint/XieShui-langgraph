from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from aiopath import AsyncPath
from typing import Any, Dict
import jinja2

from src.graph_manager.utils.state import MainAgentState


async def init_information(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    启动节点，在该节点中注入系统提示词、任务书
    """
    # 读取提示词
    system_prompt_path: AsyncPath = AsyncPath(__file__).parent.parent / "instruction.txt"
    system_prompt: str = (await system_prompt_path.read_text(encoding="utf-8")).strip()

    # 注入系统提示词
    system_prompt = jinja2.Template(system_prompt).render({
        "user_instruction": config.get("configurable", {}).get("extra_system_prompt", "")
    })

    # 注入任务书
    task_prompt = "# 知识图谱管理任务指令\n\n" + state.get("task_book", "")

    # 读取 planning.txt
    planning_prompt_path: AsyncPath = AsyncPath(__file__).parent / "planning.txt"
    planning_prompt: str = (await planning_prompt_path.read_text(encoding="utf-8")).strip()

    return {"messages": [
        SystemMessage(content=system_prompt),
        HumanMessage(content=task_prompt),
        HumanMessage(content=planning_prompt)
    ]}