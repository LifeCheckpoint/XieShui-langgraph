"""
榭水 Agent 运行主图
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from typing import Literal

# 配置 LLM
from src.main_agent.llm_manager import LLMConfig, initialize_llm_manager

testing_LLM_mode: Literal["normal", "advance"] = "advance"

if testing_LLM_mode == "normal":
    initialize_llm_manager({
        "default": LLMConfig(),
        "default_moretoken": LLMConfig(max_tokens=65536),
        "summarization": LLMConfig(temperature=0.2),
        "agent_execution": LLMConfig(temperature=0.3),
        "tools": LLMConfig(temperature=0.3, max_tokens=4096),
        "long_writing": LLMConfig(model_name="google/gemini-2.5-flash", temperature=0.5, max_tokens=65536, frequency_penalty=0.4),
    })
elif testing_LLM_mode == "advance":
    initialize_llm_manager({
        "default": LLMConfig(model_name="anthropic/claude-sonnet-4"),
        "default_moretoken": LLMConfig(model_name="anthropic/claude-sonnet-4", max_tokens=100000),
        "summarization": LLMConfig(model_name="google/gemini-2.5-flash", temperature=0.2, frequency_penalty=0.4),
        "agent_execution": LLMConfig(model_name="anthropic/claude-sonnet-4", temperature=0.35),
        "tools": LLMConfig(model_name="anthropic/claude-sonnet-4", temperature=0.3, max_tokens=4096),
        "long_writing": LLMConfig(model_name="google/gemini-2.5-flash", temperature=0.5, max_tokens=65536, frequency_penalty=0.4),
    })
else:
    raise ValueError(f"Unsupported testing_LLM_mode: {testing_LLM_mode}. Supported modes are 'normal' and 'advance'.")

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
    ask_interrupt,
    summarization_node,
    tools,
    deep_research_node,
    graph_manager_node,
)

# 主图定义
builder = StateGraph(MainAgentState, config_schema=Configuration)

# 添加节点
builder.add_node("welcome", welcome)
builder.add_node("finish_interrupt", finish_interrupt)
builder.add_node("agent_execution", agent_execution)
builder.add_node("no_tools_warning", no_tools_warning)
builder.add_node("ask_interrupt", ask_interrupt)
builder.add_node("tools", tools)
builder.add_node("summarization", summarization_node)
builder.add_node("deep_research_node", deep_research_node)
builder.add_node("graph_manager_node", graph_manager_node)

# 添加边
builder.add_edge(START, "welcome")
builder.add_edge("welcome", "finish_interrupt")
builder.add_edge("finish_interrupt", "agent_execution")
builder.add_conditional_edges("agent_execution", should_tool, ["tools", "no_tools_warning"])
builder.add_conditional_edges("tools", tool_result_transport, ["summarization", "agent_execution", "ask_interrupt", "deep_research_node", "graph_manager_node"])
builder.add_edge("ask_interrupt", "agent_execution")
builder.add_edge("no_tools_warning", "agent_execution")
builder.add_edge("summarization", "finish_interrupt")
builder.add_edge("deep_research_node", "agent_execution")
builder.add_edge("graph_manager_node", "agent_execution")

# 编译
builder.compile(name="XieshuiMainAgent", checkpointer=MemorySaver())

__all__ = ["builder"]