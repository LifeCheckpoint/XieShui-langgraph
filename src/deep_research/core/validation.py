"""
Deep Research 数据验证模块
提供状态转换和研究数据的验证功能
"""

from typing import Any, Dict, List, Optional
from src.deep_research.utils.state import MainAgentState, ResearchCycleState
from src.deep_research.core.errors import ValidationError, StateTransitionError


def validate_state_transition(state: MainAgentState, next_node: str) -> bool:
    """
    验证状态转换是否合法
    
    Args:
        state: 当前主状态
        next_node: 下一个节点名称
        
    Returns:
        bool: 转换是否合法
        
    Raises:
        StateTransitionError: 状态转换不合法时抛出
    """
    try:
        # 验证基本状态结构
        if not isinstance(state, dict):
            raise StateTransitionError(
                "State must be a dictionary",
                str(type(state)),
                "dict"
            )
        
        # 验证必需字段
        required_fields = ["messages", "topic", "research_cycles"]
        for field in required_fields:
            if field not in state:
                raise StateTransitionError(
                    f"Missing required field: {field}",
                    "incomplete_state",
                    "complete_state"
                )
        
        # 验证研究循环状态
        research_cycles = state.get("research_cycles", [])
        if not isinstance(research_cycles, list):
            raise StateTransitionError(
                "research_cycles must be a list",
                str(type(research_cycles)),
                "list"
            )
        
        # 根据下一个节点验证特定条件
        if next_node == "plan_research":
            # 确保有研究循环
            if not research_cycles:
                raise StateTransitionError(
                    "Cannot plan research without initialized cycles",
                    "no_cycles",
                    "initialized_cycles"
                )
        
        elif next_node == "generate_search_queries":
            # 确保当前循环有研究计划
            current_cycle = research_cycles[-1] if research_cycles else {}
            if not current_cycle.get("research_plan"):
                raise StateTransitionError(
                    "Cannot generate search queries without research plan",
                    "no_research_plan",
                    "research_plan_exists"
                )
        
        elif next_node == "execute_search":
            # 确保有搜索查询
            current_cycle = research_cycles[-1] if research_cycles else {}
            if not current_cycle.get("search_queries"):
                raise StateTransitionError(
                    "Cannot execute search without search queries",
                    "no_search_queries",
                    "search_queries_exist"
                )
        
        elif next_node == "filter_search_results":
            # 确保有搜索结果
            current_cycle = research_cycles[-1] if research_cycles else {}
            if not current_cycle.get("search_results"):
                raise StateTransitionError(
                    "Cannot filter results without search results",
                    "no_search_results",
                    "search_results_exist"
                )
        
        elif next_node == "read_and_summarize":
            # 确保有筛选后的URL列表
            current_cycle = research_cycles[-1] if research_cycles else {}
            reading_list = current_cycle.get("reading_list", [])
            skimming_list = current_cycle.get("skimming_list", [])
            if not reading_list and not skimming_list:
                raise StateTransitionError(
                    "Cannot read and summarize without URLs",
                    "no_urls",
                    "urls_exist"
                )
        
        elif next_node == "generate_outline":
            # 确保有足够的研究发现
            total_findings = sum(len(cycle.get("findings", [])) for cycle in research_cycles)
            if total_findings == 0:
                raise StateTransitionError(
                    "Cannot generate outline without research findings",
                    "no_findings",
                    "findings_exist"
                )
        
        elif next_node == "write_sections":
            # 确保有报告大纲
            if not state.get("report_outline"):
                raise StateTransitionError(
                    "Cannot write sections without report outline",
                    "no_outline",
                    "outline_exists"
                )
        
        elif next_node == "finetune_report":
            # 确保有初始报告
            if not state.get("report"):
                raise StateTransitionError(
                    "Cannot finetune without initial report",
                    "no_report",
                    "report_exists"
                )
        
        return True
        
    except StateTransitionError:
        raise
    except Exception as e:
        raise StateTransitionError(
            f"Validation error: {e}",
            "validation_error",
            "valid_state"
        )


# 移除未使用的验证函数，只保留核心的状态转换验证和循环状态验证


def validate_cycle_state(cycle: ResearchCycleState) -> bool:
    """验证单个研究循环状态"""
    if not isinstance(cycle, dict):
        raise ValidationError("Research cycle must be a dictionary", "cycle", cycle)
    
    required_fields = ["cycle_count"]
    for field in required_fields:
        if field not in cycle:
            raise ValidationError(f"Missing field {field} in research cycle", field)
    
    if not isinstance(cycle["cycle_count"], int) or cycle["cycle_count"] <= 0:
        raise ValidationError("cycle_count must be a positive integer", "cycle_count", cycle["cycle_count"])
    
    return True