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

async def read_and_summarize_page(url: str, topic: str, research_plan: dict) -> str:
    """读取单个网页并进行总结"""
    try:
        # 使用 requests 获取网页内容
        response = await asyncio.to_thread(requests.get, url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status() # 如果请求失败则抛出异常
        
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 提取文本内容，可以根据需要进行更精细的提取
        # 例如，只提取 <article> 或 <main> 标签下的内容
        for script in soup(["script", "style"]):
            script.decompose()
        original_text = soup.get_text(separator='\n', strip=True)
        
    except Exception as e:
        return f"Error reading {url}: {e}"

    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "rewrite.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    
    template = jinja2.Template(prompt_template_str)

    # 为 original_text 设置一个截断，取首尾最大长度 / 2，中间省略
    max_length = 120000
    if len(original_text) > max_length:
        half_length = max_length // 2
        original_text = original_text[:half_length] + "..." + original_text[-half_length:]
    
    rendered_prompt = template.render({
        "topic": topic,
        "research_plan": research_plan,
        "original_text": original_text
    })
    
    llm = llm_manager.get_llm(config_name="default").with_structured_output(RewriteResult)
    
    response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
    
    return response.summary

async def read_and_summarize(state: MainAgentState) -> dict:
    """读取并总结精读列表中的所有网页"""
    current_cycle = state["research_cycles"][-1]
    reading_list = current_cycle.get("reading_list", [])
    topic = state["topic"]
    research_plan = current_cycle.get("research_plan", {})
    
    tasks = [read_and_summarize_page(url, topic, research_plan) for url in reading_list]
    
    summaries = await asyncio.gather(*tasks)
    
    current_cycle["findings"] = summaries
    
    return {"research_cycles": state["research_cycles"]}