from __future__ import annotations

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from aiopath import AsyncPath
import asyncio
import requests
from bs4 import BeautifulSoup
import jinja2

from src.deep_research.utils.state import MainAgentState
from src.main_agent.llm_manager import llm_manager

# --- Read and Summarize ---

class RewriteResult(BaseModel):
    rewrite: bool = Field(..., description="是否需要转写")
    content: str | None = Field(None, description="转写后的内容")
    summary: str = Field(..., description="对文本的简短摘要")

async def summarize_text(text: str, topic: str, research_plan: dict, url: str) -> str:
    """对给定文本进行重写"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "rewrite.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    
    template = jinja2.Template(prompt_template_str)

    # 为 original_text 设置一个截断，取首尾最大长度 / 2，中间省略
    max_length = 120000
    if len(text) > max_length:
        half_length = max_length // 2
        text = text[:half_length] + "..." + text[-half_length:]
    
    rendered_prompt = template.render({
        "topic": topic,
        "research_plan": research_plan,
        "original_text": text
    })
    
    llm = llm_manager.get_llm(config_name="long_writing").with_structured_output(RewriteResult)
    
    try:
        response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
    except Exception as e:
        print(f"Error invoking LLM: {e}")
        return {"raw_text": text, "summary": text[:497] + "...", "url": url}
    
    return {"raw_text": text, "summary": response.summary, "url": url}

async def read_and_summarize_page(url: str, topic: str, research_plan: dict) -> str:
    """读取单个网页并进行总结"""
    try:
        # 使用 requests 获取网页内容
        response = await asyncio.to_thread(requests.get, url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status() # 如果请求失败则抛出异常
        
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 提取文本内容
        for script in soup(["script", "style"]):
            script.decompose()
        original_text = soup.get_text(separator='\n', strip=True)
        
        return await summarize_text(original_text, topic, research_plan, url)
        
    except Exception as e:
        return f"Error reading {url}: {e}"

async def read_and_summarize(state: MainAgentState) -> dict:
    """读取并总结精读和略读列表中的所有网页"""
    current_cycle = state["research_cycles"][-1]
    reading_list = current_cycle.get("reading_list", [])
    skimming_list = current_cycle.get("skimming_list", [])
    search_results = current_cycle.get("search_results", [])
    topic = state["topic"]
    research_plan = current_cycle.get("research_plan", {})

    # 创建一个 URL 到 raw_content 的映射
    raw_content_map = {res["url"]: res["raw_content"] for res in search_results if res.get("raw_content")}

    tasks = []
    # 处理精读列表
    for url in reading_list:
        if url in raw_content_map:
            tasks.append(summarize_text(raw_content_map[url], topic, research_plan, url))
        else:
            # 如果精读列表中的 URL 没有 raw_content，则像略读列表一样处理
            tasks.append(read_and_summarize_page(url, topic, research_plan))

    # 处理略读列表
    for url in skimming_list:
        tasks.append(read_and_summarize_page(url, topic, research_plan))
    
    summaries = await asyncio.gather(*tasks)
    
    current_cycle["findings"] = [summary for summary in summaries if isinstance(summary, dict) and "summary" in summary]
    current_cycle["summary_raw_content"] = summaries
    
    return {"research_cycles": state["research_cycles"]}