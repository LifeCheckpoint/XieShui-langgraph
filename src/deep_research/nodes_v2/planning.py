"""
Deep Research Planning 节点 - 重构版本
使用新的服务抽象层，消除重复代码
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.deep_research.utils.state import MainAgentState
from src.deep_research.services.llm_service import llm_service
from src.deep_research.services.state_manager import state_manager
from src.deep_research.services.config_manager import config_manager


# 保持原有的模型定义，确保向后兼容
class ResearchPlan(BaseModel):
    research_status: str = Field(..., description="研究现状。例: 无，我即将开始研究（仅轮次为1时，不允许产生任何已研究幻觉）/ 我已经完成了关于…的研究，但是在…领域存在空白，并且尚未进行关于…的研究 / …")
    research_goal: str = Field(..., description="研究目标。例: 深入探讨QML算法的广度及其未来的发展方向")
    research_range: str = Field(..., description="研究范围。例: 我正在着手对量子机器学习（QML）的理论领域进行全面回顾，重点关注过去8到10年（2015-2025）的研究进展")
    research_method: str = Field(..., description="研究方法。例: 我将首先从…入手，通过…，特别是针对…，来…。我计划涵盖…等。此外，我还会…。我还会收集…，最终将所有收集到的信息综合成一份全面的综述")


class SearchQuery(BaseModel):
    content: str = Field(..., description="要搜索的内容")
    reason: str = Field(..., description="进行此搜索的原因")
    max_result: int = Field(..., description="期望的最大结果数")


class SearchQueries(BaseModel):
    queries: list[SearchQuery]


async def plan_research(state: MainAgentState) -> dict:
    """
    根据当前状态制定研究计划
    
    重构后的实现：
    - 移除了200+行的重复错误处理代码
    - 使用统一的LLM服务和状态管理
    - 保持完全相同的业务逻辑和返回格式
    """
    # 添加新轮次
    state_manager.add_new_cycle(state)

    # 使用状态管理器进行验证和数据准备
    state_manager.validate_transition_to(state, "plan_research")
    
    # 自适应裁剪findings以避免token溢出
    adapted_cycles = _adapt_cycles_for_token_limit(
        state["research_cycles"], 
        config_manager.research.max_token_length
    )
    
    # 准备模板上下文
    context = {
        "topic": state["topic"],
        "research_cycles": adapted_cycles,
        "research_total_cycles": state.get("research_total_cycles", 5),
        "current_cycle_index": len(state["research_cycles"]) + 1
    }
    
    # 使用LLM服务进行调用（自动处理重试和错误）
    llm_config = config_manager.get_llm_config_for_task("planning")
    response = await llm_service.invoke_with_template(
        "research_plan.txt",
        context,
        ResearchPlan,
        llm_config
    )
    
    # 使用状态管理器更新状态
    plan_data = response.model_dump()
    return state_manager.update_research_plan(state, plan_data)


async def generate_search_queries(state: MainAgentState) -> dict:
    """
    根据研究计划生成搜索查询
    
    重构后的实现：
    - 移除了重复的错误处理逻辑
    - 使用统一的服务进行状态管理和LLM调用
    """
    import datetime
    from pathlib import Path
    
    # 创建调试日志
    log_file = Path("src/deep_research/logs/debug_generate_search_queries.log")
    log_file.parent.mkdir(exist_ok=True)
    
    def write_log(message: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    write_log("=== generate_search_queries 开始 ===")
    write_log(f"输入状态keys: {list(state.keys())}")
    write_log(f"topic: {state.get('topic', 'None')}")
    write_log(f"当前research_cycles长度: {len(state.get('research_cycles', []))}")
    
    # 验证状态转换
    state_manager.validate_transition_to(state, "generate_search_queries")
    write_log("状态转换验证通过")
    
    # 获取当前循环的研究计划
    current_cycle = state_manager.get_current_cycle(state)
    write_log(f"当前循环keys: {list(current_cycle.keys())}")
    write_log(f"研究计划: {current_cycle.get('research_plan', 'None')}")
    
    # 准备模板上下文
    context = {
        "topic": state["topic"],
        "research_plan": current_cycle["research_plan"]
    }
    write_log(f"模板上下文: {context}")
    
    # 使用LLM服务生成搜索查询
    llm_config = config_manager.get_llm_config_for_task("searching")
    response_text: str = await llm_service.invoke_with_template_simple(
        "search_instruction.txt",
        context,
        llm_config
    )
    write_log(f"LLM响应类型: {type(response_text)}")
    write_log(f"LLM响应: {str(response_text)}")

    # 反序列化 str 到 SearchQueries
    import json
    obj_search_queries_data = json.loads(response_text)
    distributed_q: list = []
    for query in obj_search_queries_data["queries"]:
        distributed_q.append(SearchQuery(**query))
    
    response = SearchQueries(queries=distributed_q)
    
    # 安全地提取搜索查询
    if hasattr(response, 'queries') and getattr(response, 'queries', None):
        # 直接访问属性
        search_queries = [query.model_dump() for query in getattr(response, 'queries', [])]  # type: ignore
        write_log(f"提取查询数量(直接访问): {len(search_queries)}")
    else:
        # 通过字典访问
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else {}
        write_log(f"响应字典内容: {response_dict}")
        queries = response_dict.get('queries', [])
        search_queries = [q if isinstance(q, dict) else q.model_dump() for q in queries]
        write_log(f"提取查询数量(字典访问): {len(search_queries)}")
    
    write_log(f"search_queries: {search_queries}")
    
    # 更新状态
    result = state_manager.update_search_queries(state, search_queries)
    write_log(f"状态更新结果keys: {list(result.keys())}")
    write_log(f"更新后的research_cycles长度: {state_manager.get_cycle_count(state)}")
    
    if result.get('research_cycles'):
        updated_cycle = result['research_cycles'][-1]
        write_log(f"更新后当前循环的search_queries: {updated_cycle.get('search_queries', 'None')}")
    
    write_log("=== generate_search_queries 结束 ===")
    return result


def _adapt_cycles_for_token_limit(research_cycles: list, max_token_length: int = 128000) -> list:
    """
    自适应裁剪研究循环数据以避免token溢出
    
    从原来的重复实现中提取出来，成为独立的工具函数
    """
    adapted_cycles = []
    
    # 统计所有findings的总长度
    total_finding_count = sum(len(cycle.get("findings", [])) for cycle in research_cycles)
    total_finding_length = sum(
        len(str(finding)) 
        for cycle in research_cycles 
        for finding in cycle.get("findings", [])
    )
    
    # 如果超过限制，按比例裁剪
    if total_finding_length > max_token_length and total_finding_count > 0:
        max_finding_length = 100000 // total_finding_count
        
        for cycle in research_cycles:
            adapted_cycle = cycle.copy()
            findings = cycle.get("findings", [])
            
            if findings:
                adapted_findings = []
                for finding in findings:
                    finding_str = str(finding)
                    if len(finding_str) > max_finding_length:
                        adapted_findings.append(finding_str[:max_finding_length] + "...")
                    else:
                        adapted_findings.append(finding)
                adapted_cycle["findings"] = adapted_findings
            
            adapted_cycles.append(adapted_cycle)
    else:
        adapted_cycles = research_cycles
    
    return adapted_cycles


# 为了完全向后兼容，保留原有的便捷函数接口
async def invoke_research_plan_legacy(topic: str, research_cycles: list, total_cycles: int) -> ResearchPlan:
    """向后兼容的研究计划生成函数"""
    adapted_cycles = _adapt_cycles_for_token_limit(research_cycles)
    
    context = {
        "topic": topic,
        "research_cycles": adapted_cycles,
        "research_total_cycles": total_cycles,
        "current_cycle_index": len(research_cycles) + 1
    }
    
    response = await llm_service.invoke_with_template(
        "research_plan.txt",
        context,
        ResearchPlan
    )
    return response  # type: ignore


async def invoke_search_queries_legacy(topic: str, research_plan: dict) -> SearchQueries:
    """向后兼容的搜索查询生成函数"""
    context = {
        "topic": topic,
        "research_plan": research_plan
    }
    
    response = await llm_service.invoke_with_template(
        "search_instruction.txt",
        context,
        SearchQueries
    )
    return response  # type: ignore