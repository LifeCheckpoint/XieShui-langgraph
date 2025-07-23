from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage
from typing import Any, Dict

from src.graph_manager.utils.state import MainAgentState

def should_tool(state: MainAgentState, config: RunnableConfig) -> str:
    """
    检查是否需要调用工具。
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    
    # 如果没有工具调用，添加警告并循环回到 agent_execution
    state.messages.append(HumanMessage(
        content="目前尚未调用任何工具，如果你认为任务已经结束，请调用attempt_completion或klgraph_abort工具；否则请继续尝试利用工具进行知识图谱管理"
    ))
    
    return "agent_execution"

def tool_result_transport(state: MainAgentState, config: RunnableConfig) -> str:
    """
    通过工具调用确定下一步 Agent 的转移执行情况。
    """
    messages = state["messages"]
    ai_message = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            ai_message = msg
            break
    
    if ai_message and ai_message.tool_calls:
        for tool_call in ai_message.tool_calls:
            match tool_call["name"]:
                case "attempt_completion":
                    # 任务完成，结束流程
                    return "__end__"
                case "klgraph_abort":
                    # 任务中止，结束流程
                    return "__end__"
    
    # 其他工具调用后，继续执行
    return "agent_execution"