"""
Deep Research Searching 节点 - 重构版本
使用新的服务抽象层，大幅简化代码
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_tavily import TavilySearch

from src.deep_research.utils.state import MainAgentState
from src.deep_research.services.llm_service import llm_service
from src.deep_research.services.state_manager import state_manager
from src.deep_research.services.config_manager import config_manager


class FilteredURLs(BaseModel):
    reading_list: list[str] = Field(..., description="筛选后用于精读的URL列表")
    skimming_list: list[str] = Field(..., description="筛选后用于略读的URL列表")
    ignore_list: list[str] = Field(..., description="筛选后忽略的URL列表")


async def execute_search(state: MainAgentState) -> dict:
    """
    执行搜索查询
    """
    import datetime
    from pathlib import Path
    
    # 创建调试日志
    log_file = Path("src/deep_research/logs/debug_execute_search.log")
    log_file.parent.mkdir(exist_ok=True)
    
    def write_log(message: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    write_log("=== execute_search 开始 ===")
    write_log(f"输入状态keys: {list(state.keys())}")
    write_log(f"topic: {state.get('topic', 'None')}")
    write_log(f"research_cycles长度: {len(state.get('research_cycles', []))}")
    
    if state.get('research_cycles'):
        current_cycle = state['research_cycles'][-1]
        write_log(f"当前循环keys: {list(current_cycle.keys())}")
        write_log(f"当前循环search_queries: {current_cycle.get('search_queries', 'None')}")
        write_log(f"search_queries长度: {len(current_cycle.get('search_queries', []))}")
        if current_cycle.get('search_queries'):
            write_log(f"第一个查询: {current_cycle['search_queries'][0]}")
    else:
        write_log("没有研究循环!")
    
    # 验证状态转换
    try:
        state_manager.validate_transition_to(state, "execute_search")
        write_log("状态转换验证通过")
    except Exception as e:
        write_log(f"状态转换验证失败: {e}")
        raise
    
    # 获取当前循环和搜索配置
    current_cycle = state_manager.get_current_cycle(state)
    search_queries = current_cycle.get("search_queries", [])
    search_config = config_manager.get_search_config()
    
    # 执行所有搜索查询
    all_results = []
    for query in search_queries:
        # 使用配置中的参数
        max_results = query.get("max_result", search_config["default_results"])
        
        tavily = TavilySearch(
            max_results=max_results,
            topic="general",
            include_raw_content=True,
        )
        
        try:
            results = tavily.invoke({"query": query["content"]})
            all_results.extend(results.get("results", []))
        except Exception as e:
            # 搜索失败时记录但不中断流程
            print(f"Search failed for query '{query['content']}': {e}")
            continue
    
    # 使用状态管理器更新搜索结果
    return state_manager.update_search_results(state, all_results)


async def filter_search_results(state: MainAgentState) -> dict:
    """
    根据研究计划筛选搜索结果
    
    重构后的实现：
    - 移除了100+行的重复错误处理代码
    - 使用统一的LLM服务进行筛选
    - 保持完全相同的筛选逻辑和格式
    """
    # 验证状态转换
    state_manager.validate_transition_to(state, "filter_search_results")
    
    # 获取当前循环数据
    current_cycle = state_manager.get_current_cycle(state)
    search_results = current_cycle.get("search_results", [])
    
    if not search_results:
        # 如果没有搜索结果，返回空列表
        return state_manager.update_filtered_urls(state, [], [])
    
    # 准备简化的搜索结果（节省token）
    simplified_results = [
        {"url": res["url"], "title": res.get("title", "No title")}
        for res in search_results
        if "url" in res
    ]
    
    # 准备模板上下文
    context = {
        "research_plan": current_cycle["research_plan"],
        "search_result": simplified_results
    }
    
    # 使用LLM服务进行筛选
    llm_config = config_manager.get_llm_config_for_task("searching")
    response = await llm_service.invoke_with_template(
        "search_filter.txt",
        context,
        FilteredURLs,
        llm_config
    )
    
    # 安全地提取结果
    if hasattr(response, 'reading_list'):
        reading_list = response.reading_list  # type: ignore
        skimming_list = response.skimming_list  # type: ignore
    else:
        # 降级处理 - 转换为字典
        result_dict = response.model_dump() if hasattr(response, 'model_dump') else {}
        reading_list = result_dict.get("reading_list", [])
        skimming_list = result_dict.get("skimming_list", [])
    
    return state_manager.update_filtered_urls(state, reading_list, skimming_list)


def _validate_search_results(search_results: list) -> bool:
    """验证搜索结果的有效性"""
    if not isinstance(search_results, list):
        return False
    
    for result in search_results:
        if not isinstance(result, dict) or "url" not in result:
            return False
    
    return True


def _apply_search_limits(search_results: list, max_results: int) -> list:
    """应用搜索结果数量限制"""
    if len(search_results) <= max_results:
        return search_results
    
    # 保留前max_results个结果
    return search_results[:max_results]


def _deduplicate_search_results(search_results: list) -> list:
    """去除重复的搜索结果"""
    seen_urls = set()
    deduplicated = []
    
    for result in search_results:
        url = result.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduplicated.append(result)
    
    return deduplicated


# 为了向后兼容，提供原有接口的包装函数
async def execute_search_legacy(search_queries: list) -> list:
    """向后兼容的搜索执行函数"""
    all_results = []
    
    for query in search_queries:
        tavily = TavilySearch(
            max_results=query.get("max_result", 5),
            topic="general",
            include_raw_content=True,
        )
        
        try:
            results = tavily.invoke({"query": query["content"]})
            all_results.extend(results.get("results", []))
        except Exception:
            continue
    
    return all_results


async def filter_search_results_legacy(
    research_plan: dict, 
    search_results: list
) -> FilteredURLs:
    """向后兼容的搜索结果筛选函数"""
    simplified_results = [
        {"url": res["url"], "title": res.get("title", "No title")}
        for res in search_results
        if "url" in res
    ]
    
    context = {
        "research_plan": research_plan,
        "search_result": simplified_results
    }
    
    response = await llm_service.invoke_with_template(
        "search_filter.txt",
        context,
        FilteredURLs
    )
    
    return response  # type: ignore