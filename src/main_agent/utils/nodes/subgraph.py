from __future__ import annotations

import traceback
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import ToolMessage
from langchain_core.messages import AIMessage, HumanMessage
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState
from src.deep_research.graph import graph as deep_research_graph
from src.graph_manager import graph_manager_builder

async def deep_research_node(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    深度研究节点，用于处理深度研究任务的状态和消息。
    """

    param = {}
    
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
                case "deep_research":
                    # 处理 deep_research 工具调用
                    param = {
                        "subject": tool_call["args"].get("subject", ""),
                        "recursion": tool_call["args"].get("recursion", 3)
                    }

    if param:
        # 有参数，开始执行
        try:
            result = await deep_research_graph.ainvoke({
                "messages": [HumanMessage(content=tool_call["args"].get("subject", ""))],
                "topic": param["subject"],
                "research_total_cycles": int(param["recursion"])
            }) # type: ignore
        except Exception as e:
            error_msg = "深度研究执行过程中发生异常: " + str(e) + "\n" + traceback.format_exc()
            return {
                "messages": [ToolMessage(
                    tool_call_id="deep_research",
                    content=error_msg,
                )]
            }
    else:
        # 没有参数，返回警告消息
        return {
            "messages": [ToolMessage(
                tool_call_id="deep_research",
                content="没有提供研究主题或轮次，请先使用 `deep_research` 工具调用进行设置",
            )]
        }
    
    # 返回结果
    return {
        "messages": [ToolMessage(
            tool_call_id="deep_research",
            content=result.get("report", "深度研究报告生成失败，请检查日志获取更多信息"),
        )],
    }


async def graph_manager_node(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    知识图谱管理节点，用于处理知识图谱管理任务的状态和消息。
    """

    param = {}
    
    messages = state.messages
    # 查找最近的 AIMessage
    ai_message = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            ai_message = msg
            break
    
    if ai_message and ai_message.tool_calls:
        for tool_call in ai_message.tool_calls:
            if tool_call["name"] == "graph_manager":
                param = {
                    "task_book": tool_call["args"].get("task_book", ""),
                }
                break

    if param:
        # 有参数，开始执行
        try:
            result = await graph_manager_builder.ainvoke({
                "messages": [], # graph_manager 是一个独立的 Agent，不需要传递消息历史
                "task_book": param["task_book"],
            }, {"recursion_limit": 100}) # type: ignore
            # 获取 graph_manager 的最终结果
            final_message = result["messages"][-1]
            content = final_message.content
        except Exception as e:
            content = "知识图谱管理执行过程中发生异常: " + str(e) + "\n" + traceback.format_exc()
    else:
        # 没有参数，返回警告消息
        content = "没有提供任务书，请先使用 `graph_manager` 工具调用进行设置"
    
    # 返回结果
    return {
        "messages": [ToolMessage(
            tool_call_id="graph_manager",
            content=content,
        )],
    }
