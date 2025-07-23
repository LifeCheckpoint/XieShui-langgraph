from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph_manager.utils.state import MainAgentState
from src.graph_manager.utils.tools import tools
from src.graph_manager.utils.nodes.graph_agent import init_information
from src.graph_manager.utils.nodes.execution import agent_execution
from src.graph_manager.utils.nodes.routing import should_tool, tool_result_transport

# 主图定义
builder = StateGraph(MainAgentState)

# 添加节点
builder.add_node("init_information", init_information)
builder.add_node("agent_execution", agent_execution)
builder.add_node("tools", tools)

# 添加边
builder.add_edge(START, "init_information")
builder.add_edge("init_information", "agent_execution")

# 条件边：根据 agent_execution 的结果，决定是调用工具还是继续执行
builder.add_conditional_edges(
    "agent_execution",
    should_tool,
    {
        "tools": "tools",
        "agent_execution": "agent_execution"
    }
)

# 条件边：根据 tools 的结果，决定是结束还是继续执行
builder.add_conditional_edges(
    "tools",
    tool_result_transport,
    {
        "__end__": END,
        "agent_execution": "agent_execution"
    }
)

# 编译
graph_manager_builder = builder.compile(checkpointer=MemorySaver())

__all__ = ["graph_manager_builder"]
