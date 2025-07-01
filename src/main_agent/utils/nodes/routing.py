from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState


def should_tool(state: MainAgentState, config: RunnableConfig) -> str:
    """
    检查是否需要调用工具，如果最后一条消息：
    - 包含工具调用，则返回 "tools" 表示进入工具节点
    - 否则返回 "no_tools_warning" 进入工具未调用警告节点
    """
    messages = state.messages
    last_message = messages[-1]
    # 只有 AIMessage 才会有 tool_calls 属性
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "no_tools_warning"


def tool_result_transport(state: MainAgentState, config: RunnableConfig) -> str:
    """
    通过工具调用确定下一步 Agent 的转移执行情况
    """
    messages = state.messages
    # 查找最近的 AIMessage，因为只有 AIMessage 才会有 tool_calls 属性
    ai_message = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            ai_message = msg
            break
    
    if ai_message and ai_message.tool_calls:
        for tool_call in ai_message.tool_calls:
            
            # 检查是否有工具调用
            match tool_call["name"]:
                case "attempt_completion":
                    return "summarization"
                case "ask_question":
                    return "ask_interrupt"
    
    return "agent_execution"