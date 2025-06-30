from __future__ import annotations

from langgraph.types import interrupt
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, ToolMessage
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState


async def finish_interrupt(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    暂停 Agent 运行，直到用户发起下一次对话
    """
    next_input = interrupt("向我对话以继续...")
    return {"messages": [HumanMessage(content=next_input)]}


async def ask_interrupt(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    中断并询问用户问题
    """
    # 获取最近一条 ask_question 工具调用的内容
    for msg in reversed(state.messages):
        if isinstance(msg, ToolMessage):
            question_and_choices = msg.content
            break

    user_input = interrupt(question_and_choices)
    return {"messages": [HumanMessage(content="用户回答：" + user_input)]}