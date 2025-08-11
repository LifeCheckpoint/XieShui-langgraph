"""
Deep Research Routing 节点 - 重构版本
保持原有路由逻辑，使用新的状态管理服务
"""

from __future__ import annotations

from src.deep_research.utils.state import MainAgentState
from src.deep_research.services.state_manager import state_manager
from src.deep_research.services.config_manager import config_manager


def initialize_research(state: MainAgentState) -> dict:
    """
    初始化研究状态
    """
    # 从消息中提取主题
    topic = state["messages"][-1].content
    
    # 使用配置管理器获取研究参数
    research_config = config_manager.research
    total_cycles = state.get("research_total_cycles", research_config.max_research_cycles)
    
    return {
        "topic": topic,
        "research_total_cycles": int(total_cycles),
        "research_cycles": []
    }

def update_and_check_cycle(state: MainAgentState) -> str:
    """
    更新并检查循环次数，决定下一步走向
    """
    # 使用状态管理器检查研究是否完成
    if state_manager.is_research_complete(state):
        return "generate_report"
    else:
        return "plan_research"

def should_continue_research(state: MainAgentState) -> bool:
    """
    检查是否应该继续研究
    
    Args:
        state: 主状态
        
    Returns:
        bool: 是否继续研究
    """
    return not state_manager.is_research_complete(state)


def get_next_cycle_data() -> dict:
    """
    获取下一个循环的初始数据
    
    Returns:
        dict: 新循环的初始数据结构
    """
    return {
        "research_plan": {},
        "search_queries": [],
        "search_results": [],
        "reading_list": [],
        "skimming_list": [],
        "findings": [],
        "summary_raw_content": {}
    }


def validate_research_state(state: MainAgentState) -> bool:
    """
    验证研究状态的完整性
    
    Args:
        state: 主状态
        
    Returns:
        bool: 状态是否有效
    """
    try:
        # 使用状态管理器进行验证
        state_manager.validate_transition_to(state, "any")
        return True
    except Exception:
        return False



# 为了向后兼容，保留原有的函数接口
def initialize_research_legacy(topic: str, total_cycles: int = 5) -> dict:
    """向后兼容的研究初始化函数"""
    initial_cycle = {
        "cycle_count": 1,
        "research_plan": {},
        "search_queries": [],
        "search_results": [],
        "reading_list": [],
        "findings": []
    }
    
    return {
        "topic": topic,
        "research_total_cycles": int(total_cycles),
        "research_cycles": [initial_cycle]
    }


def check_cycle_completion_legacy(current_cycles: int, total_cycles: int) -> str:
    """向后兼容的循环检查函数"""
    if current_cycles >= total_cycles:
        return "generate_report"
    else:
        return "plan_research"


def create_new_cycle_legacy(cycle_count: int) -> dict:
    """向后兼容的新循环创建函数"""
    return {
        "cycle_count": cycle_count,
        "research_plan": {},
        "search_queries": [],
        "search_results": [],
        "reading_list": [],
        "findings": []
    }