"""
榭水 Agent 运行主图
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from utils import (
    # state
    MainAgentState,

    # config
    Configuration,

    # nodes
    welcome,
    finish_interrupt,
    agent_execution,
)


builder = StateGraph(MainAgentState, config_schema=Configuration)

# 添加节点
builder.add_node("welcome", welcome)
builder.add_node("finish_interrupt", finish_interrupt)
builder.add_node("agent_execution", agent_execution)

# 添加边
builder.add_edge(START, "welcome")
builder.add_edge("welcome", "finish_interrupt")
builder.add_edge("finish_interrupt", "agent_execution")

# 编译
builder.compile(name="XieshuiMainAgent", checkpointer=MemorySaver())
