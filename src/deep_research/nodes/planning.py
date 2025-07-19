from __future__ import annotations

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from aiopath import AsyncPath
import jinja2

from src.deep_research.utils.state import MainAgentState
from src.main_agent.llm_manager import llm_manager

# --- Research Plan ---

class ResearchPlan(BaseModel):
    research_goal: str = Field(..., description="研究目标。例: 深入探讨QML算法的广度及其未来的发展方向")
    research_range: str = Field(..., description="研究范围。例: 我正在着手对量子机器学习（QML）的理论领域进行全面回顾，重点关注过去8到10年（2015-2025）的研究进展")
    research_method: str = Field(..., description="研究方法。例: 我将首先从…入手，通过…，特别是针对…，来…。我计划涵盖…等。此外，我还会…。我还会收集…，最终将所有收集到的信息综合成一份全面的综述")

async def plan_research(state: MainAgentState) -> dict:
    """根据当前状态制定研究计划"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "research_plan.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    
    template = jinja2.Template(prompt_template_str)
    
    rendered_prompt = template.render({
        "topic": state["topic"],
        "research_cycles": state["research_cycles"],
        "research_total_cycles": state.get("research_total_cycles", 5),
        "current_cycle_index": len(state["research_cycles"]) + 1
    })
    
    llm = llm_manager.get_llm(config_name="default").with_structured_output(ResearchPlan)
    
    response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
    
    current_cycle = state["research_cycles"][-1]
    current_cycle["research_plan"] = response.dict()
    
    return {"research_cycles": state["research_cycles"]}

# --- Search Queries ---

class SearchQuery(BaseModel):
    content: str = Field(..., description="要搜索的内容")
    reason: str = Field(..., description="进行此搜索的原因")
    max_result: int = Field(..., description="期望的最大结果数")

class SearchQueries(BaseModel):
    queries: list[SearchQuery]

async def generate_search_queries(state: MainAgentState) -> dict:
    """根据研究计划生成搜索查询"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "search_instruction.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    
    template = jinja2.Template(prompt_template_str)
    
    current_cycle = state["research_cycles"][-1]
    
    rendered_prompt = template.render({
        "topic": state["topic"],
        "research_plan": current_cycle["research_plan"]
    })
    
    llm = llm_manager.get_llm(config_name="default").with_structured_output(SearchQueries)
    
    response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
    
    current_cycle["search_queries"] = [q.dict() for q in response.queries]
    
    return {"research_cycles": state["research_cycles"]}