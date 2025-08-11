"""
Deep Research 状态管理器
提供统一的状态访问和更新接口
"""

from typing import Dict, List, Any, Optional
from copy import deepcopy

from src.deep_research.utils.state import MainAgentState, ResearchCycleState
from src.deep_research.core.validation import validate_state_transition, validate_cycle_state
from src.deep_research.core.errors import StateTransitionError, ValidationError


class ResearchStateManager:
    """研究状态管理器"""
    
    def __init__(self):
        self._state_history: List[Dict[str, Any]] = []
    
    def get_current_cycle(self, state: MainAgentState) -> ResearchCycleState:
        """
        获取当前研究循环
        
        Args:
            state: 主状态
            
        Returns:
            ResearchCycleState: 当前循环状态
        """
        research_cycles = state.get("research_cycles", [])
        if not research_cycles:
            raise StateTransitionError(
                "No research cycles available",
                "empty_cycles",
                "initialized_cycles"
            )
        
        return research_cycles[-1]
    
    def get_cycle_by_index(self, state: MainAgentState, index: int) -> ResearchCycleState:
        """
        根据索引获取研究循环
        
        Args:
            state: 主状态
            index: 循环索引
            
        Returns:
            ResearchCycleState: 指定循环状态
        """
        research_cycles = state.get("research_cycles", [])
        if index < 0 or index >= len(research_cycles):
            raise StateTransitionError(
                f"Invalid cycle index: {index}",
                f"index_{index}",
                f"valid_index_0_to_{len(research_cycles)-1}"
            )
        
        return research_cycles[index]
    
    def update_current_cycle(
        self,
        state: MainAgentState,
        **updates
    ) -> Dict[str, List[ResearchCycleState]]:
        """
        更新当前研究循环
        
        Args:
            state: 主状态
            **updates: 要更新的字段
            
        Returns:
            Dict: 包含更新后的research_cycles的字典
        """
        research_cycles = state.get("research_cycles", [])
        if not research_cycles:
            raise StateTransitionError(
                "Cannot update cycle - no cycles available",
                "empty_cycles",
                "initialized_cycles"
            )
        
        # 获取当前循环并更新（使用字典合并而不是update）
        current_cycle = research_cycles[-1].copy()
        updated_cycle = {**current_cycle, **updates}  # type: ignore
        
        # 验证更新后的循环状态
        validate_cycle_state(updated_cycle)  # type: ignore
        
        # 更新状态
        updated_cycles = research_cycles[:-1] + [updated_cycle]  # type: ignore
        
        # 记录状态变更历史
        self._record_state_change(state, "update_current_cycle", updates)
        
        return {"research_cycles": updated_cycles}  # type: ignore
    
    def add_new_cycle(
        self,
        state: MainAgentState,
        cycle_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[ResearchCycleState]]:
        """
        添加新的研究循环
        
        Args:
            state: 主状态
            cycle_data: 新循环的初始数据
            
        Returns:
            Dict: 包含更新后的research_cycles的字典
        """
        research_cycles = state.get("research_cycles", [])
        current_cycle_count = len(research_cycles)
        
        # 创建新循环
        new_cycle = {
            "cycle_count": current_cycle_count + 1,
            "research_plan": {},
            "search_queries": [],
            "search_results": [],
            "reading_list": [],
            "skimming_list": [],
            "findings": [],
            "summary_raw_content": {}
        }
        
        # 应用提供的数据（使用字典合并）
        if cycle_data:
            new_cycle = {**new_cycle, **cycle_data}  # type: ignore
        
        # 验证新循环状态
        validate_cycle_state(new_cycle)  # type: ignore
        
        # 添加到循环列表
        updated_cycles = research_cycles + [new_cycle]  # type: ignore
        
        # 记录状态变更历史
        self._record_state_change(state, "add_new_cycle", {"cycle_count": new_cycle["cycle_count"]})
        
        return {"research_cycles": updated_cycles}  # type: ignore
    
    def update_research_plan(
        self,
        state: MainAgentState,
        research_plan: Dict[str, Any]
    ) -> Dict[str, List[ResearchCycleState]]:
        """
        更新当前循环的研究计划
        
        Args:
            state: 主状态
            research_plan: 研究计划数据
            
        Returns:
            Dict: 包含更新后的research_cycles的字典
        """
        return self.update_current_cycle(state, **{"research_plan": research_plan})
    
    def update_search_queries(
        self,
        state: MainAgentState,
        search_queries: List[Dict[str, Any]]
    ) -> Dict[str, List[ResearchCycleState]]:
        """
        更新当前循环的搜索查询
        
        Args:
            state: 主状态
            search_queries: 搜索查询列表
            
        Returns:
            Dict: 包含更新后的research_cycles的字典
        """
        return self.update_current_cycle(state, **{"search_queries": search_queries})
    
    def update_search_results(
        self,
        state: MainAgentState,
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, List[ResearchCycleState]]:
        """
        更新当前循环的搜索结果
        
        Args:
            state: 主状态
            search_results: 搜索结果列表
            
        Returns:
            Dict: 包含更新后的research_cycles的字典
        """
        return self.update_current_cycle(state, **{"search_results": search_results})
    
    def update_filtered_urls(
        self,
        state: MainAgentState,
        reading_list: List[str],
        skimming_list: List[str]
    ) -> Dict[str, List[ResearchCycleState]]:
        """
        更新当前循环的筛选URL列表
        
        Args:
            state: 主状态
            reading_list: 精读URL列表
            skimming_list: 略读URL列表
            
        Returns:
            Dict: 包含更新后的research_cycles的字典
        """
        return self.update_current_cycle(
            state,
            **{"reading_list": reading_list, "skimming_list": skimming_list}
        )
    
    def update_findings(
        self,
        state: MainAgentState,
        findings: List[Dict[str, Any]],
        summary_raw_content: Optional[List[Any]] = None
    ) -> Dict[str, List[ResearchCycleState]]:
        """
        更新当前循环的研究发现
        
        Args:
            state: 主状态
            findings: 研究发现列表
            summary_raw_content: 原始内容摘要
            
        Returns:
            Dict: 包含更新后的research_cycles的字典
        """
        updates = {"findings": findings}
        if summary_raw_content is not None:
            updates["summary_raw_content"] = summary_raw_content
        
        return self.update_current_cycle(state, **updates)
    
    def get_all_findings(self, state: MainAgentState) -> List[Dict[str, Any]]:
        """
        获取所有循环的研究发现
        
        Args:
            state: 主状态
            
        Returns:
            List: 所有研究发现
        """
        all_findings = []
        for cycle in state.get("research_cycles", []):
            all_findings.extend(cycle.get("findings", []))
        return all_findings
    
    def get_all_search_queries(self, state: MainAgentState) -> List[str]:
        """
        获取所有循环的搜索查询
        
        Args:
            state: 主状态
            
        Returns:
            List: 所有搜索查询内容
        """
        all_queries = []
        for cycle in state.get("research_cycles", []):
            for query in cycle.get("search_queries", []):
                if isinstance(query, dict) and "content" in query:
                    all_queries.append(query["content"])
                elif isinstance(query, str):
                    all_queries.append(query)
        return all_queries
    
    def get_cycle_count(self, state: MainAgentState) -> int:
        """
        获取当前循环数量
        
        Args:
            state: 主状态
            
        Returns:
            int: 循环数量
        """
        return len(state.get("research_cycles", []))
    
    def is_research_complete(self, state: MainAgentState) -> bool:
        """
        检查研究是否完成
        
        Args:
            state: 主状态
            
        Returns:
            bool: 是否完成
        """
        current_cycles = self.get_cycle_count(state)
        total_cycles = state.get("research_total_cycles", 5)
        return current_cycles >= total_cycles
    
    def validate_transition_to(self, state: MainAgentState, next_node: str) -> bool:
        """
        验证到下一个节点的状态转换
        
        Args:
            state: 当前状态
            next_node: 下一个节点名称
            
        Returns:
            bool: 转换是否有效
        """
        return validate_state_transition(state, next_node)
    
    def create_state_snapshot(self, state: MainAgentState) -> Dict[str, Any]:
        """
        创建状态快照
        
        Args:
            state: 主状态
            
        Returns:
            Dict: 状态快照
        """
        return deepcopy(dict(state))  # type: ignore
    
    def restore_state_snapshot(self, snapshot: Dict[str, Any]) -> MainAgentState:
        """
        恢复状态快照
        
        Args:
            snapshot: 状态快照
            
        Returns:
            MainAgentState: 恢复的状态
        """
        return deepcopy(snapshot)  # type: ignore
    
    def get_state_summary(self, state: MainAgentState) -> Dict[str, Any]:
        """
        获取状态摘要信息
        
        Args:
            state: 主状态
            
        Returns:
            Dict: 状态摘要
        """
        cycles = state.get("research_cycles", [])
        total_findings = sum(len(cycle.get("findings", [])) for cycle in cycles)
        total_queries = sum(len(cycle.get("search_queries", [])) for cycle in cycles)
        
        return {
            "topic": state.get("topic", ""),
            "cycle_count": len(cycles),
            "total_cycles": state.get("research_total_cycles", 5),
            "total_findings": total_findings,
            "total_queries": total_queries,
            "has_outline": bool(state.get("report_outline")),
            "has_report": bool(state.get("report")),
            "has_citations": bool(state.get("citations"))
        }
    
    def _record_state_change(
        self,
        state: MainAgentState,
        operation: str,
        details: Dict[str, Any]
    ) -> None:
        """记录状态变更历史"""
        try:
            import datetime
            history_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "operation": operation,
                "details": details,
                "cycle_count": self.get_cycle_count(state)
            }
            self._state_history.append(history_entry)
            
            # 保持历史记录不超过100条
            if len(self._state_history) > 100:
                self._state_history = self._state_history[-100:]
        except Exception:
            # 静默忽略历史记录错误
            pass
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """获取状态变更历史"""
        return self._state_history.copy()
    
    def clear_state_history(self) -> None:
        """清空状态变更历史"""
        self._state_history.clear()


# 全局状态管理器实例
state_manager = ResearchStateManager()