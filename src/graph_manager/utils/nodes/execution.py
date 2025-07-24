from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from typing import Any, Dict

from src.graph_manager.utils.state import MainAgentState
from src.graph_manager.utils.tools import tool_list
from src.main_agent.llm_manager import llm_manager # 复用 main_agent 的 LLM 管理器

async def agent_execution(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Agent 执行节点，处理用户输入并执行任务
    """
    # 注意：这里我们复用了 main_agent 的 llm_manager
    # 在实际应用中，可以考虑为 graph_manager 定义独立的 LLM 配置
    llm = llm_manager.get_llm(config_name="default").bind_tools(tool_list)
    response = await llm.ainvoke(state.messages)
    return {"messages": [response]}