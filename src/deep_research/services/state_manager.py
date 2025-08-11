"""
Deep Research 状态管理器 - 简化版本
提供基本的状态访问和更新接口
"""

from typing import Dict, List, Any
from src.deep_research.utils.state import MainAgentState, ResearchCycleState
from src.deep_research.core.validation import validate_state_transition
from src.deep_research.core.errors import StateTransitionError


class ResearchStateManager:
    """研究状态管理器"""
    
    def get_current_cycle(self, state: MainAgentState) -> ResearchCycleState:
        """获取当前研究循环"""
        research_cycles = state.get("research_cycles", [])
        if not research_cycles:
            raise StateTransitionError(
                "No research cycles available",
                "empty_cycles",
                "initialized_cycles"
            )
        return research_cycles[-1]
    
    def get_cycle_count(self, state: MainAgentState) -> int:
        """获取当前循环数量"""
        return len(state.get("research_cycles", []))
    
    def is_research_complete(self, state: MainAgentState) -> bool:
        """检查研究是否完成"""
        current_cycles = self.get_cycle_count(state)
        total_cycles = state.get("research_total_cycles", 3)
        return current_cycles >= total_cycles
    
    def update_current_cycle(self, state: MainAgentState, **updates) -> Dict[str, Any]:
        """更新当前研究循环"""
        research_cycles = state.get("research_cycles", [])
        if not research_cycles:
            raise StateTransitionError(
                "Cannot update cycle - no cycles available",
                "empty_cycles",
                "initialized_cycles"
            )
        
        # 更新最后一个循环
        current_cycle = research_cycles[-1].copy()
        current_cycle = {**current_cycle, **updates}  # type: ignore
        
        # 返回更新后的循环列表
        updated_cycles = research_cycles[:-1] + [current_cycle]  # type: ignore
        return {"research_cycles": updated_cycles}
    
    def add_new_cycle(self, state: MainAgentState):
        """添加新的研究循环"""
        research_cycles = state.get("research_cycles", [])
        cycle_count = len(research_cycles) + 1
        
        new_cycle = {
            "cycle_count": cycle_count,
            "research_plan": {},
            "search_queries": [],
            "search_results": [],
            "reading_list": [],
            "skimming_list": [],
            "findings": [],
            "summary_raw_content": {}
        }
        new_cycle_typed = ResearchCycleState(**new_cycle)
        
        updated_cycles = research_cycles + [new_cycle_typed]
        state["research_cycles"] = updated_cycles
    
    def update_research_plan(self, state: MainAgentState, research_plan: Dict[str, Any]) -> Dict[str, Any]:
        """更新研究计划"""
        return self.update_current_cycle(state, research_plan=research_plan)
    
    def update_search_queries(self, state: MainAgentState, search_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """更新搜索查询"""
        return self.update_current_cycle(state, search_queries=search_queries)
    
    def update_search_results(self, state: MainAgentState, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """更新搜索结果"""
        return self.update_current_cycle(state, search_results=search_results)
    
    def update_filtered_urls(self, state: MainAgentState, reading_list: List[str], skimming_list: List[str]) -> Dict[str, Any]:
        """更新筛选URL列表"""
        return self.update_current_cycle(state, reading_list=reading_list, skimming_list=skimming_list)
    
    def get_all_search_queries(self, state: MainAgentState) -> List:
        """从 state 获取所有搜索记录"""
        all_queries = []
        for cycle in state.get("research_cycles", []):
            all_queries.extend(cycle.get("search_queries", []))
        return all_queries
    
    def update_findings(self, state: MainAgentState, findings: List[Dict[str, Any]], summary_raw_content: Any = None) -> Dict[str, Any]:
        """更新研究发现"""
        updates = {"findings": findings}
        if summary_raw_content is not None:
            updates["summary_raw_content"] = summary_raw_content
        return self.update_current_cycle(state, **updates)
    
    def validate_transition_to(self, state: MainAgentState, next_node: str) -> bool:
        """验证状态转换"""
        return validate_state_transition(state, next_node)


# 全局状态管理器实例
state_manager = ResearchStateManager()