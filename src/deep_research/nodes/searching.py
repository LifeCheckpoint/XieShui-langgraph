from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from aiopath import AsyncPath
from langchain_tavily import TavilySearch

from src.deep_research.utils.state import MainAgentState
from src.main_agent.llm_manager import llm_manager

# --- Execute Search ---

async def execute_search(state: MainAgentState) -> dict:
    """执行搜索查询"""
    tavily = TavilySearch(
        max_results=query["max_result"],
        topic="general",
        include_raw_content=True,
    )
    
    current_cycle = state["research_cycles"][-1]
    search_queries = current_cycle.get("search_queries", [])
    
    all_results = []
    for query in search_queries:
        results = tavily.invoke({"query": query["content"]})
        all_results.extend(results.get("results", []))
        
    current_cycle["search_results"] = all_results
    
    return {"research_cycles": state["research_cycles"]}

# --- Filter Search Results ---

class FilteredURLs(BaseModel):
    urls: list[str] = Field(..., description="筛选后用于精读的URL列表")

async def filter_search_results(state: MainAgentState) -> dict:
    """根据研究计划筛选搜索结果"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "search_filter.txt"
    prompt_template = await prompt_path.read_text(encoding="utf-8")
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    llm = llm_manager.get_llm(config_name="default").with_structured_output(FilteredURLs)
    
    chain = prompt | llm
    
    current_cycle = state["research_cycles"][-1]
    
    # 为了节省 token，只将 URL 和标题传递给 LLM
    simplified_results = [
        {"url": res["url"], "title": res["title"]} 
        for res in current_cycle.get("search_results", [])
    ]
    
    response = await chain.ainvoke({
        "research_plan": current_cycle["research_plan"],
        "search_result": simplified_results
    })
    
    current_cycle["reading_list"] = response.urls
    
    return {"research_cycles": state["research_cycles"]}