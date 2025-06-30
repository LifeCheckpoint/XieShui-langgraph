"""
Main Agent 的节点定义

Agent 将在这些节点之间进行切换，处理任务
"""

from __future__ import annotations

from langgraph.types import interrupt
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from aiopath import AsyncPath
from typing import Any, Dict

from src.main_agent.utils.state import MainAgentState
from src.main_agent.utils.tools import tool_list


async def welcome(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    欢迎节点，在该节点中注入系统提示词与欢迎信息
    """
    # 读取提示词
    system_prompt_path: AsyncPath = AsyncPath(__file__).parent / "instruction.txt"
    system_prompt: str = (await system_prompt_path.read_text(encoding="utf-8")).strip()

    # 替换模板
    system_prompt = system_prompt.replace("<<user_instruction>>", config.get("configurable", {}).get("extra_system_prompt", ""))

    # 注入系统提示词
    return {"messages": [SystemMessage(content=system_prompt)]}


async def finish_interrupt(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    暂停 Agent 运行，直到用户发起下一次对话
    """
    next_input = interrupt("向我对话以继续...")
    return {"messages": [HumanMessage(content=next_input)]}


async def ask_interrupt(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    中断并询问用户问题
    """
    # 获取最近一条 ask_question 工具调用的内容
    for msg in reversed(state.messages):
        if isinstance(msg, ToolMessage):
            question_and_choices = msg.content
            break

    user_input = interrupt(question_and_choices)
    return {"messages": [HumanMessage(content=user_input)]}

async def agent_execution(state: MainAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Agent 执行节点，处理用户输入并执行任务
    """
    llm = ChatOpenAI(
        model="google/gemini-2.5-flash",
        temperature=0.55,
        base_url="https://openrouter.ai/api/v1",
        api_key=(await (AsyncPath(__file__).parent / "api_key").read_text(encoding="utf-8")).strip(),
        max_retries=3,
        max_tokens=8192,
    ).bind_tools(tool_list) # TODO: 更灵活的模型配置
    
    response = await llm.ainvoke(state.messages)
    return {"messages": [response]}


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
                    return "finish_interrupt"
                case "ask_question":
                    return "ask_interrupt"
    
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
    "should_tool", "no_tools_warning", "tool_result_transport"
]
