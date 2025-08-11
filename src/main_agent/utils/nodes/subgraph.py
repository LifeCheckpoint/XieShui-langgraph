from __future__ import annotations

import traceback
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import ToolMessage
from langchain_core.messages import AIMessage, HumanMessage
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState
from src.deep_research.graph_v2 import graph as deep_research_graph
from src.graph_manager import graph_manager_builder

async def deep_research_node(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    深度研究节点，用于处理深度研究任务的状态和消息。
    """
    import uuid
    from pathlib import Path

    param = {}
    tool_call_id = None
    
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
                    tool_call_id = tool_call["id"]
                    break

    # 生成唯一的执行ID用于日志跟踪
    execution_id = str(uuid.uuid4())[:8]
    log_file = Path(__file__).parent / f"deep_research_execution_{execution_id}.log"
    
    # 记录执行开始
    log_file.write_text(f"Deep research execution started - ID: {execution_id}\nTool call ID: {tool_call_id}\nParam: {param}\n", encoding="utf-8")

    if not param:
        # 没有参数，返回警告消息
        error_msg = "没有提供研究主题或轮次，请先使用 `deep_research` 工具调用进行设置"
        log_file.write_text(log_file.read_text(encoding="utf-8") + f"No parameters provided - {error_msg}\n", encoding="utf-8")
        return {
            "messages": [ToolMessage(
                tool_call_id=tool_call_id or "deep_research",
                content=error_msg,
            )]
        }

    # 有参数，开始执行
    try:
        log_file.write_text(log_file.read_text(encoding="utf-8") + f"Starting deep research execution with subject: {param['subject']}\n", encoding="utf-8")
        
        result = await deep_research_graph.ainvoke({
            "messages": [HumanMessage(content=tool_call["args"].get("subject", ""))],
            "topic": param["subject"],
            "research_total_cycles": int(param["recursion"])
        }) # type: ignore
        
        # 执行成功，记录日志并返回结果
        success_msg = result.get("report", "深度研究报告生成失败，请检查日志获取更多信息")
        log_file.write_text(log_file.read_text(encoding="utf-8") + f"Deep research completed successfully\nResult length: {len(success_msg)}\n", encoding="utf-8")
        
        return {
            "messages": [ToolMessage(
                tool_call_id=tool_call_id or "deep_research",
                content=success_msg,
            )],
        }
        
    except Exception as e:
        # 执行失败，记录详细错误并返回
        error_msg = "深度研究执行过程中发生异常: " + str(e) + "\n" + traceback.format_exc()
        log_file.write_text(log_file.read_text(encoding="utf-8") + f"Deep research failed with exception: {e}\nFull traceback: {traceback.format_exc()}\n", encoding="utf-8")
        
        return {
            "messages": [ToolMessage(
                tool_call_id=tool_call_id or "deep_research",
                content=error_msg,
            )]
        }


async def graph_manager_node(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    知识图谱管理节点，用于处理知识图谱管理任务的状态和消息。
    """
    import uuid
    from pathlib import Path

    param = {}
    tool_call_id = None
    
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
                tool_call_id = tool_call["id"]
                break

    # 生成唯一的执行ID用于日志跟踪
    execution_id = str(uuid.uuid4())[:8]
    log_file = Path(__file__).parent / f"graph_manager_execution_{execution_id}.log"
    
    # 记录执行开始
    log_file.write_text(f"Graph manager execution started - ID: {execution_id}\nTool call ID: {tool_call_id}\nParam: {param}\n", encoding="utf-8")

    if not param:
        # 没有参数，返回警告消息
        error_msg = "没有提供任务书，请先使用 `graph_manager` 工具调用进行设置"
        log_file.write_text(log_file.read_text(encoding="utf-8") + f"No parameters provided - {error_msg}\n", encoding="utf-8")
        return {
            "messages": [ToolMessage(
                tool_call_id=tool_call_id or "graph_manager",
                content=error_msg,
            )],
        }

    # 有参数，开始执行
    try:
        log_file.write_text(log_file.read_text(encoding="utf-8") + f"Starting graph manager execution with task_book: {param['task_book'][:100]}...\n", encoding="utf-8")
        
        result = await graph_manager_builder.ainvoke({
            "messages": [], # graph_manager 是一个独立的 Agent，不需要传递消息历史
            "task_book": param["task_book"],
        }, {"recursion_limit": 100}) # type: ignore
        
        # 检查子图返回的消息是否包含重复的tool_call_id
        returned_messages = result.get("messages", [])
        log_file.write_text(log_file.read_text(encoding="utf-8") + f"Graph manager completed, returned {len(returned_messages)} messages\n", encoding="utf-8")
        
        # 检查返回的消息中是否有与当前tool_call_id冲突的ToolMessage
        conflicting_messages = []
        for msg in returned_messages:
            if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id') and msg.tool_call_id == tool_call_id:
                conflicting_messages.append(msg)
                
        if conflicting_messages:
            # 发现冲突的消息，记录警告并修复
            log_file.write_text(log_file.read_text(encoding="utf-8") + f"WARNING: Found {len(conflicting_messages)} conflicting tool_call_id messages\n", encoding="utf-8")
            # 为冲突的消息生成新的ID
            for msg in conflicting_messages:
                if hasattr(msg, 'tool_call_id'):
                    old_id = msg.tool_call_id
                    new_id = f"{old_id}_subgraph_{execution_id}"
                    msg.tool_call_id = new_id
                    log_file.write_text(log_file.read_text(encoding="utf-8") + f"Changed tool_call_id from {old_id} to {new_id}\n", encoding="utf-8")
        
        # 直接返回子图的消息，其中已经包含了正确的 ToolMessage
        return {"messages": returned_messages}
        
    except Exception as e:
        # 执行失败，记录详细错误并返回
        error_msg = "知识图谱管理执行过程中发生异常: " + str(e) + "\n" + traceback.format_exc()
        log_file.write_text(log_file.read_text(encoding="utf-8") + f"Graph manager failed with exception: {e}\nFull traceback: {traceback.format_exc()}\n", encoding="utf-8")
        
        return {
            "messages": [ToolMessage(
                tool_call_id=tool_call_id or "graph_manager",
                content=error_msg,
            )],
        }
