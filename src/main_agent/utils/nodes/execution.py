from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.messages.utils import count_tokens_approximately
from langmem.short_term import SummarizationNode
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState
from src.main_agent.utils.tools import tool_list
from src.main_agent.utils.llm_manager import llm_manager


summarization_node = SummarizationNode(
    token_counter=count_tokens_approximately,
    model=llm_manager.get_llm(config_name="summarization"),
    max_tokens=16384,
    max_tokens_before_summary=65536,
    max_summary_tokens=4096,
)


async def agent_execution(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Agent 执行节点，处理用户输入并执行任务
    """
    llm = llm_manager.get_llm(config_name="agent_execution").bind_tools(tool_list)    
    response = llm.invoke(state.messages)
    return {"messages": [response]}