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
    write_log("开始获取当前循环和搜索配置")
    try:
        current_cycle = state_manager.get_current_cycle(state)
        write_log("成功获取当前循环")
    except Exception as e:
        write_log(f"获取当前循环失败: {e}")
        raise
    
    search_queries = current_cycle.get("search_queries", [])
    write_log(f"获取到{len(search_queries)}个搜索查询")
    
    try:
        search_config = config_manager.get_search_config()
        write_log(f"成功获取搜索配置: {search_config}")
    except Exception as e:
        write_log(f"获取搜索配置失败: {e}")
        raise
    
    # === 诊断日志：验证搜索问题 ===
    write_log("=== 诊断：执行搜索查询 ===")
    
    # 检查Tavily配置
    import os
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    write_log(f"Tavily API Key存在: {'是' if tavily_api_key else '否'}")
    if tavily_api_key:
        write_log(f"Tavily API Key长度: {len(tavily_api_key)}")
        write_log(f"Tavily API Key前缀: {tavily_api_key[:10]}...")
    
    # 执行所有搜索查询
    all_results = []
    for i, query in enumerate(search_queries):
        write_log(f"执行第{i+1}个查询: {query['content']}")
        
        # 使用配置中的参数
        max_results = query.get("max_result", search_config["default_results"])
        write_log(f"最大结果数: {max_results}")
        
        try:
            write_log("初始化TavilySearch")
            tavily = TavilySearch(
                max_results=max_results,
                topic="general",
                include_raw_content=True,
            )
            write_log("TavilySearch初始化成功")
            
            write_log(f"开始调用tavily.invoke")
            results = tavily.invoke({"query": query["content"]})
            write_log(f"搜索成功完成，结果类型: {type(results)}")
            write_log(f"结果keys: {list(results.keys()) if results else 'None'}")
            
            if results and "results" in results:
                query_results = results.get("results", [])
                write_log(f"查询{i+1}获得{len(query_results)}个结果")
                all_results.extend(query_results)
                
                # 记录第一个结果的摘要信息
                if query_results:
                    first_result = query_results[0]
                    write_log(f"第一个结果URL: {first_result.get('url', 'N/A')}")
                    write_log(f"第一个结果标题: {first_result.get('title', 'N/A')}")
            else:
                write_log(f"查询{i+1}没有获得有效结果")
                
        except Exception as e:
            write_log(f"查询{i+1}失败，错误类型: {type(e).__name__}")
            write_log(f"查询{i+1}失败，错误详情: {e}")
            import traceback
            write_log(f"查询{i+1}失败，完整错误堆栈: {traceback.format_exc()}")
            # 搜索失败时记录但不中断流程
            print(f"Search failed for query '{query['content']}': {e}")
            continue
    
    write_log(f"所有搜索完成，总共获得{len(all_results)}个结果")
    
    # 使用状态管理器更新搜索结果
    try:
        write_log("开始更新状态中的搜索结果")
        result = state_manager.update_search_results(state, all_results)
        write_log("搜索结果更新成功")
        write_log("=== execute_search 结束 ===")
        return result
    except Exception as e:
        write_log(f"更新搜索结果失败: {e}")
        import traceback
        write_log(f"更新搜索结果失败，完整错误堆栈: {traceback.format_exc()}")
        raise


async def filter_search_results(state: MainAgentState) -> dict:
    """
    根据研究计划筛选搜索结果
    
    重构后的实现：
    - 移除了100+行的重复错误处理代码
    - 使用统一的LLM服务进行筛选
    - 保持完全相同的筛选逻辑和格式
    """
    import datetime
    from pathlib import Path
    
    # 创建调试日志
    log_file = Path("src/deep_research/logs/debug_filter_search_results.log")
    log_file.parent.mkdir(exist_ok=True)
    
    def write_log(message: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    write_log("=== filter_search_results 开始 ===")
    
    # 验证状态转换
    try:
        state_manager.validate_transition_to(state, "filter_search_results")
        write_log("状态转换验证通过")
    except Exception as e:
        write_log(f"状态转换验证失败: {e}")
        raise
    
    # 获取当前循环数据
    try:
        current_cycle = state_manager.get_current_cycle(state)
        write_log("成功获取当前循环")
    except Exception as e:
        write_log(f"获取当前循环失败: {e}")
        raise
    
    search_results = current_cycle.get("search_results", [])
    write_log(f"获取到{len(search_results)}个搜索结果")
    
    if not search_results:
        write_log("搜索结果为空，返回空URL列表")
        # 如果没有搜索结果，返回空列表
        return state_manager.update_filtered_urls(state, [], [])
    
    # 准备简化的搜索结果（节省token）
    simplified_results = [
        {"url": res["url"], "title": res.get("title", "No title")}
        for res in search_results
        if "url" in res
    ]
    write_log(f"简化后的搜索结果数量: {len(simplified_results)}")
    
    # 记录前几个搜索结果
    if simplified_results:
        write_log(f"第一个搜索结果: {simplified_results[0]}")
        if len(simplified_results) > 1:
            write_log(f"第二个搜索结果: {simplified_results[1]}")
    
    # 准备模板上下文
    context = {
        "research_plan": current_cycle["research_plan"],
        "search_result": simplified_results
    }
    write_log(f"模板上下文准备完成，研究计划长度: {len(str(context['research_plan']))}")
    
    # === 诊断日志：验证LLM筛选问题 ===
    write_log("=== 诊断：执行LLM筛选 ===")
    
    # 使用LLM服务进行筛选
    try:
        write_log("开始获取LLM配置")
        llm_config = config_manager.get_llm_config_for_task("searching")
        write_log(f"LLM配置: {llm_config}")
        
        write_log("开始调用LLM服务进行筛选")
        response = await llm_service.invoke_with_template(
            "search_filter.txt",
            context,
            FilteredURLs,
            llm_config
        )
        write_log("LLM筛选调用成功")
        write_log(f"LLM响应类型: {type(response)}")
        write_log(f"LLM响应内容: {response}")
        
        # 检查是否返回空字典 - 如果是，进行降级处理
        if isinstance(response, dict) and len(response) == 0:
            write_log("检测到结构化调用返回空字典，切换到简单调用降级处理")
            
            # 使用简单调用作为降级方案
            write_log("开始降级处理：使用简单调用")
            simple_response = await llm_service.invoke_with_template_simple(
                "search_filter.txt",
                context,
                llm_config
            )
            write_log(f"简单调用响应类型: {type(simple_response)}")
            write_log(f"简单调用响应长度: {len(simple_response) if simple_response else 0}")
            write_log(f"简单调用响应前100字符: {repr(simple_response[:100]) if simple_response else 'N/A'}")
            
            # 清理可能的markdown标记（和之前修复JSON问题一样）
            cleaned_response = simple_response.strip() if simple_response else ""
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]  # 移除开始标记
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]  # 移除结束标记
            cleaned_response = cleaned_response.strip()
            
            write_log(f"清理后响应长度: {len(cleaned_response)}")
            
            # 手动解析JSON
            import json
            try:
                parsed_response = json.loads(cleaned_response)
                write_log("手动JSON解析成功")
                write_log(f"解析结果: {parsed_response}")
                
                # 创建FilteredURLs实例
                reading_list = parsed_response.get("reading_list", [])
                skimming_list = parsed_response.get("skimming_list", [])
                ignore_list = parsed_response.get("ignore_list", [])
                
                response = FilteredURLs(
                    reading_list=reading_list,
                    skimming_list=skimming_list,
                    ignore_list=ignore_list
                )
                write_log(f"降级处理成功，创建FilteredURLs实例: reading={len(reading_list)}, skimming={len(skimming_list)}")
                
            except json.JSONDecodeError as e:
                write_log(f"手动JSON解析失败: {e}")
                write_log(f"尝试解析的文本: {repr(cleaned_response[:200])}")
                # 如果JSON解析也失败，返回空列表避免完全失败
                response = FilteredURLs(reading_list=[], skimming_list=[], ignore_list=[])
                write_log("JSON解析失败，返回空URL列表作为最后降级")
        
        # 检查响应属性
        if hasattr(response, 'reading_list'):
            write_log(f"LLM响应有reading_list属性")
            write_log(f"reading_list内容: {getattr(response, 'reading_list', 'N/A')}")
        if hasattr(response, 'skimming_list'):
            write_log(f"LLM响应有skimming_list属性")
            write_log(f"skimming_list内容: {getattr(response, 'skimming_list', 'N/A')}")
        if hasattr(response, 'ignore_list'):
            write_log(f"LLM响应有ignore_list属性")
            write_log(f"ignore_list内容: {getattr(response, 'ignore_list', 'N/A')}")
        
    except Exception as e:
        write_log(f"LLM筛选失败，错误类型: {type(e).__name__}")
        write_log(f"LLM筛选失败，错误详情: {e}")
        import traceback
        write_log(f"LLM筛选失败，完整错误堆栈: {traceback.format_exc()}")
        raise
    
    # 安全地提取结果
    try:
        if hasattr(response, 'reading_list'):
            reading_list = response.reading_list  # type: ignore
            skimming_list = response.skimming_list  # type: ignore
            write_log(f"直接提取 - reading_list: {len(reading_list)}个URL")
            write_log(f"直接提取 - skimming_list: {len(skimming_list)}个URL")
            
            if reading_list:
                write_log(f"reading_list前几个: {reading_list[:3]}")
            if skimming_list:
                write_log(f"skimming_list前几个: {skimming_list[:3]}")
        else:
            # 降级处理 - 转换为字典
            write_log("无法直接提取，尝试model_dump")
            result_dict = response.model_dump() if hasattr(response, 'model_dump') else {}
            reading_list = result_dict.get("reading_list", [])
            skimming_list = result_dict.get("skimming_list", [])
            write_log(f"字典提取 - reading_list: {len(reading_list)}个URL")
            write_log(f"字典提取 - skimming_list: {len(skimming_list)}个URL")
        
        # 更新状态
        write_log("开始更新状态中的筛选URL")
        result = state_manager.update_filtered_urls(state, reading_list, skimming_list)
        write_log("筛选URL更新成功")
        write_log("=== filter_search_results 结束 ===")
        return result
    
    except Exception as e:
        write_log(f"提取筛选结果失败: {e}")
        import traceback
        write_log(f"提取筛选结果失败，完整错误堆栈: {traceback.format_exc()}")
        raise


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