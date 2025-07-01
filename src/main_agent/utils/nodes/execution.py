from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages.utils import count_tokens_approximately
from langmem.short_term import SummarizationNode
from pathlib import Path
from aiopath import AsyncPath
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState
from src.main_agent.utils.tools import tool_list


summarization_node = SummarizationNode(
    token_counter=count_tokens_approximately,
    model=ChatOpenAI(
        model="deepseek/deepseek-chat-v3-0324",
        temperature=0.3,
        base_url="https://openrouter.ai/api/v1",
        api_key=(Path(__file__).parent.parent / "api_key").read_text(encoding="utf-8").strip(),
        max_retries=3,
        max_tokens=8192,
    ), # TODO: 更灵活的模型配置
    max_tokens=16384,
    max_tokens_before_summary=65536,
    max_summary_tokens=4096,
)


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