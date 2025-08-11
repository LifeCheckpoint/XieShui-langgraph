from __future__ import annotations

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from aiopath import AsyncPath
from langchain_tavily import TavilySearch
import jinja2

from src.deep_research.utils.state import MainAgentState
from src.main_agent.llm_manager import llm_manager

# --- Execute Search ---

async def execute_search(state: MainAgentState) -> dict:
    """执行搜索查询"""
    current_cycle = state["research_cycles"][-1]
    search_queries = current_cycle.get("search_queries", [])
    
    all_results = []
    for query in search_queries:
        tavily = TavilySearch(
            max_results=query["max_result"],
            topic="general",
            include_raw_content=True,
        )
        results = tavily.invoke({"query": query["content"]})
        all_results.extend(results.get("results", []))
        
    current_cycle["search_results"] = all_results
    
    return {"research_cycles": state["research_cycles"]}

# --- Filter Search Results ---

class FilteredURLs(BaseModel):
    reading_list: list[str] = Field(..., description="筛选后用于精读的URL列表")
    skimming_list: list[str] = Field(..., description="筛选后用于略读的URL列表")
    ignore_list: list[str] = Field(..., description="筛选后忽略的URL列表") # 仅用于指导模型排除

async def filter_search_results(state: MainAgentState) -> dict:
    """根据研究计划筛选搜索结果"""
    from pathlib import Path
    
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "search_filter.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    
    template = jinja2.Template(prompt_template_str)
    
    current_cycle = state["research_cycles"][-1]
    
    # 为了节省 token，只将 URL 和标题传递给 LLM
    simplified_results = [
        {"url": res["url"], "title": res["title"]}
        for res in current_cycle.get("search_results", [])
    ]
    
    rendered_prompt = template.render({
        "research_plan": current_cycle["research_plan"],
        "search_result": simplified_results
    })
    
    llm = llm_manager.get_llm(config_name="default").with_structured_output(FilteredURLs)
    
    # 最多重试3次
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
            # 记录成功响应用于调试
            (Path(__file__).parent / "filter_search_success.log").write_text(f"Filter search response (attempt {attempt + 1}): {response}\nPrompt: {rendered_prompt}", encoding="utf-8")
            break
        except Exception as e:
            # 详细错误记录
            error_details = f"Error filtering search results (attempt {attempt + 1}): {e}\nError type: {type(e).__name__}\nPrompt: {rendered_prompt}"
            (Path(__file__).parent / "filter_search_error.log").write_text(error_details, encoding="utf-8")
            
            # 对于JSON解析错误，尝试手动解析
            if "expected value at line 1 column 1" in str(e) or "json" in str(e).lower() or "validation error" in str(e).lower():
                try:
                    # 降级到非结构化输出进行手动解析
                    fallback_llm = llm_manager.get_llm(config_name="default")
                    fallback_prompt = f"{rendered_prompt}\n\n请严格按照以下JSON格式回复，不要包含任何其他文字:\n{{\n  \"reading_list\": [\"url1\", \"url2\"],\n  \"skimming_list\": [\"url3\", \"url4\"],\n  \"ignore_list\": [\"url5\", \"url6\"]\n}}"
                    
                    fallback_response = await fallback_llm.ainvoke([HumanMessage(content=fallback_prompt)])
                    
                    # 尝试手动解析JSON
                    import json
                    try:
                        content = str(fallback_response.content).strip() if fallback_response.content else ""
                        # 移除可能的markdown代码块标记
                        if content.startswith("```json"):
                            content = content[7:]
                        if content.endswith("```"):
                            content = content[:-3]
                        content = content.strip()
                        
                        parsed_content = json.loads(content)
                        
                        # 确保所有必需的字段都存在
                        if "reading_list" not in parsed_content:
                            parsed_content["reading_list"] = []
                        if "skimming_list" not in parsed_content:
                            parsed_content["skimming_list"] = []
                        if "ignore_list" not in parsed_content:
                            parsed_content["ignore_list"] = []
                        
                        response = FilteredURLs(**parsed_content)
                        
                        # 记录手动解析成功
                        (Path(__file__).parent / "filter_search_manual_success.log").write_text(f"Manual parse successful (attempt {attempt + 1}): {response}\nOriginal error: {e}", encoding="utf-8")
                        break
                        
                    except (json.JSONDecodeError, Exception) as parse_e:
                        # 手动解析失败，记录日志
                        (Path(__file__).parent / "filter_search_manual_error.log").write_text(f"Manual parse failed (attempt {attempt + 1}): {parse_e}\nFallback content: {fallback_response.content}\nOriginal error: {e}", encoding="utf-8")
                        
                        # 如果不是最后一次尝试，继续重试
                        if attempt < max_retries - 1:
                            continue
                        else:
                            # 最后一次尝试失败，使用默认值
                            all_urls = [res["url"] for res in simplified_results]
                            # 简单启发式：前一半用于精读，后一半用于略读
                            mid_point = len(all_urls) // 2
                            response = FilteredURLs(
                                reading_list=all_urls[:mid_point] if all_urls else [],
                                skimming_list=all_urls[mid_point:] if all_urls else [],
                                ignore_list=[]
                            )
                            break
                            
                except Exception as fallback_e:
                    # 降级调用失败，记录日志
                    (Path(__file__).parent / "filter_search_fallback_error.log").write_text(f"Fallback call failed (attempt {attempt + 1}): {fallback_e}\nOriginal error: {e}", encoding="utf-8")
                    
                    # 如果不是最后一次尝试，继续重试
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # 最后一次尝试失败，使用默认值
                        all_urls = [res["url"] for res in simplified_results]
                        response = FilteredURLs(
                            reading_list=all_urls[:3] if len(all_urls) >= 3 else all_urls,
                            skimming_list=all_urls[3:] if len(all_urls) > 3 else [],
                            ignore_list=[]
                        )
                        break
            else:
                # 非JSON错误，如果不是最后一次尝试，继续重试
                if attempt < max_retries - 1:
                    continue
                else:
                    # 最后一次尝试失败，抛出异常
                    raise e
    else:
        # 如果所有尝试都失败了，抛出最后一个异常
        raise Exception(f"Failed to filter search results after {max_retries} attempts")
    
    current_cycle["reading_list"] = response.reading_list
    current_cycle["skimming_list"] = response.skimming_list
    
    return {"research_cycles": state["research_cycles"]}