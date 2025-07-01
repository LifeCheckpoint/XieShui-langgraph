from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from aiopath import AsyncPath
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState
from src.main_agent.utils.tools import tool_list


async def agent_execution(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Agent 执行节点，处理用户输入并执行任务
    """
    llm = ChatOpenAI(
        model="deepseek/deepseek-chat-v3-0324",
        temperature=0.3,
        base_url="https://openrouter.ai/api/v1",
        api_key=(await (AsyncPath(__file__).parent.parent / "api_key").read_text(encoding="utf-8")).strip(),
        max_retries=3,
        max_tokens=8192,
        # frequency_penalty=0.4,
    ).bind_tools(tool_list) # TODO: 更灵活的模型配置
    
    response = llm.invoke(state.messages)
    return {"messages": [response]}