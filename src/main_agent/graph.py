"""
榭水 Agent 运行主图
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from src.main_agent.utils import (
    # state
    MainAgentState,

    # config
    Configuration,

    # nodes
    welcome,
    finish_interrupt,
    agent_execution,
    should_tool,
    no_tools_warning,
    tool_result_transport,
    tools,
)


builder = StateGraph(MainAgentState, config_schema=Configuration)

# 添加节点
builder.add_node("welcome", welcome)
builder.add_node("finish_interrupt", finish_interrupt)
builder.add_node("agent_execution", agent_execution)
builder.add_node("no_tools_warning", no_tools_warning)
builder.add_node("tools", tools)

# 添加边
builder.add_edge(START, "welcome")
builder.add_edge("welcome", "finish_interrupt")
builder.add_edge("finish_interrupt", "agent_execution")
builder.add_conditional_edges("agent_execution", should_tool, ["tools", "no_tools_warning"]) 
builder.add_conditional_edges("tools", tool_result_transport, ["finish_interrupt", "agent_execution"])
builder.add_edge("no_tools_warning", "agent_execution")

# 编译
builder.compile(name="XieshuiMainAgent", checkpointer=MemorySaver())

__all__ = ["builder"]