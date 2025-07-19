from __future__ import annotations

from src.deep_research.utils.state import MainAgentState

# --- Routing and Control ---

def initialize_research(state: MainAgentState) -> dict:
    """初始化研究状态"""
    topic = state["messages"][-1].content
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
        "research_cycles": [initial_cycle]
    }

def update_and_check_cycle(state: MainAgentState) -> str:
    """更新并检查循环次数，决定下一步走向"""
    current_cycle_count = len(state["research_cycles"])
    
    if current_cycle_count >= state.get("research_total_cycles", 5):
        return "generate_report"
    else:
        next_cycle = {
            "cycle_count": current_cycle_count + 1,
            "research_plan": {},
            "search_queries": [],
            "search_results": [],
            "reading_list": [],
            "findings": []
        }
        state["research_cycles"].append(next_cycle)
        return "plan_research"