from __future__ import annotations

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from aiopath import AsyncPath
from pathlib import Path
import jinja2

from src.deep_research.utils.state import MainAgentState
from src.main_agent.llm_manager import llm_manager

# --- Research Plan ---

class ResearchPlan(BaseModel):
    research_status: str = Field(..., description="研究现状。例: 无，我即将开始研究（仅轮次为1时，不允许产生任何已研究幻觉）/ 我已经完成了关于…的研究，但是在…领域存在空白，并且尚未进行关于…的研究 / …")
    research_goal: str = Field(..., description="研究目标。例: 深入探讨QML算法的广度及其未来的发展方向")
    research_range: str = Field(..., description="研究范围。例: 我正在着手对量子机器学习（QML）的理论领域进行全面回顾，重点关注过去8到10年（2015-2025）的研究进展")
    research_method: str = Field(..., description="研究方法。例: 我将首先从…入手，通过…，特别是针对…，来…。我计划涵盖…等。此外，我还会…。我还会收集…，最终将所有收集到的信息综合成一份全面的综述")

async def plan_research(state: MainAgentState) -> dict:
    """根据当前状态制定研究计划"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "research_plan.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    
    template = jinja2.Template(prompt_template_str)

    # 由于会爆 token，所以自适应裁剪所有的 findings

    adapted_state = state.copy()
    # 统计所有 fidings 的总长度
    total_finding_count = sum(len(cycle.get("findings", [])) for cycle in adapted_state["research_cycles"])
    total_finding_length = sum(len(finding) for cycle in adapted_state["research_cycles"] for finding in cycle.get("findings", []))
    # 总长度超过 128000 时，强制裁剪到 100000 // total_finding_count
    if total_finding_length > 128000 and total_finding_count > 0:
        max_finding_length = 100000 // total_finding_count
        for i, cycle in enumerate(adapted_state["research_cycles"]):
            for j, finding in enumerate(cycle.get("findings", [])):
                if len(finding) > max_finding_length:
                    adapted_state["research_cycles"][i]["findings"][j] = finding[:max_finding_length] + "..."
    
    # 渲染模板

    rendered_prompt = template.render({
        "topic": adapted_state["topic"],
        "research_cycles": adapted_state["research_cycles"],
        "research_total_cycles": adapted_state.get("research_total_cycles", 5),
        "current_cycle_index": len(adapted_state["research_cycles"]) + 1
    })
    
    llm = llm_manager.get_llm(config_name="default").with_structured_output(ResearchPlan)
    
    try:
        response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
    except Exception as e:
        (Path(__file__).parent / "error.log").write_text(f"Error invoking LLM: {e}\nPrompt: {rendered_prompt}", encoding="utf-8")
        raise e
    
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