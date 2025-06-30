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

__all__ = ["welcome"]


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