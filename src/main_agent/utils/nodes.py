"""
Main Agent 的节点定义

Agent 将在这些节点之间进行切换，处理任务
"""

from __future__ import annotations

from langgraph.types import interrupt
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pathlib import Path
from typing import Any, Dict

from state import MainAgentState


async def welcome(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    欢迎节点，在该节点中注入系统提示词与欢迎信息
    """
    # 读取提示词
    system_prompt_path = Path(__file__).parent / "instruction.txt"
    
    if not system_prompt_path.exists():
        # TODO error node
        pass

    try:
        system_prompt = system_prompt_path.read_text(encoding="utf-8")

        # 替换模板
        system_prompt = system_prompt.format_map({
            "user_instruction": config.get("configurable", {}).extra_system_prompt,
        })

    except Exception as e:
        # TODO error node
        pass

    # 注入系统提示词
    return {"messages": [SystemMessage(content=system_prompt)]}


async def finish_interrupt(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    暂停 Agent 运行，直到用户发起下一次对话
    """
    next_input = interrupt("向我对话以继续...")
    return {"messages": [HumanMessage(content=next_input)]}


async def agent_execution(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Agent 执行节点，处理用户输入并执行任务
    """
    llm = ChatOpenAI(
        model="google/gemini-2.5-flash",
        temperature=0.55,
        base_url="https://openrouter.ai/api/v1",
        api_key=(Path(__file__).parent / "api_key").read_text(encoding="utf-8").strip(),
        max_retries=3,
        max_tokens=8192,
    ) # TODO: 更灵活的模型配置
    
    response = llm.invoke(state["messages"])
    return {"messages": [AIMessage(content=response.content)]}


def should_tool(state: MainAgentState, config: RunnableConfig) -> str:
    """
    检查是否需要调用工具，如果最后一条消息：
    - 包含工具调用，则返回 "tools" 表示进入工具节点
    - 否则返回 "no_tools_warning" 进入工具未调用警告节点
    """
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "no_tools_warning"


def should_finish(state: MainAgentState, config: RunnableConfig) -> str:
    """
    检查是否需要结束任务，如果最后一条消息：
    - 包含 `attempt_completion` 工具调用，则返回 "finish_interrupt" 进入中断节点
    - 否则返回 "agent_execution" 表示进入 Agent 执行节点
    """
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls and last_message.tool_calls[0].name == "attempt_completion":
        return "finish_interrupt"
    return "agent_execution"


def no_tools_warning(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    工具未调用警告节点，提示 Agent 没有调用工具
    """
    return {"messages": [HumanMessage(
        content="目前没有调用任何工具，请检查你需要调用什么工具。如果你认为当前任务已经结束，则使用 `attempt_completion` 工具向系统确认该次任务完成"
    )]}


__all__ = [
    "welcome", "finish_interrupt", "agent_execution", 
    "should_tool", "no_tools_warning", "should_finish"
]
