"""
榭水 Agent 运行主图
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from utils import (
    # state
    MainAgentState,

    # config
    Configuration,

    # nodes
    welcome,
)


builder = StateGraph(MainAgentState, config_schema=Configuration)

# 添加节点
builder.add_node("welcome", welcome)

# 添加边
builder.add_edge(START, "welcome")

# 编译
builder.compile(name="XieshuiMainAgent")
