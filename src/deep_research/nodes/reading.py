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
    from pathlib import Path
    
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
    
    # 最多重试3次
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
            # 记录成功响应用于调试
            (Path(__file__).parent / "summarize_text_success.log").write_text(f"Summarize text response (attempt {attempt + 1}): {response}\nURL: {url}", encoding="utf-8")
            break
        except Exception as e:
            # 详细错误记录
            error_details = f"Error summarizing text (attempt {attempt + 1}): {e}\nError type: {type(e).__name__}\nURL: {url}"
            (Path(__file__).parent / "summarize_text_error.log").write_text(error_details, encoding="utf-8")
            
            # 对于JSON解析错误，尝试手动解析
            if "expected value at line 1 column 1" in str(e) or "json" in str(e).lower() or "validation error" in str(e).lower():
                try:
                    # 降级到非结构化输出进行手动解析
                    fallback_llm = llm_manager.get_llm(config_name="long_writing")
                    fallback_prompt = f"{rendered_prompt}\n\n请严格按照以下JSON格式回复，不要包含任何其他文字:\n{{\n  \"rewrite\": true,\n  \"content\": \"转写后的内容（如果需要）\",\n  \"summary\": \"文本摘要\"\n}}"
                    
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
                        if "rewrite" not in parsed_content:
                            parsed_content["rewrite"] = False
                        if "summary" not in parsed_content:
                            parsed_content["summary"] = text[:497] + "..."
                        
                        response = RewriteResult(**parsed_content)
                        
                        # 记录手动解析成功
                        (Path(__file__).parent / "summarize_text_manual_success.log").write_text(f"Manual parse successful (attempt {attempt + 1}): {response}\nOriginal error: {e}", encoding="utf-8")
                        break
                        
                    except (json.JSONDecodeError, Exception) as parse_e:
                        # 手动解析失败，记录日志
                        (Path(__file__).parent / "summarize_text_manual_error.log").write_text(f"Manual parse failed (attempt {attempt + 1}): {parse_e}\nFallback content: {fallback_response.content}\nOriginal error: {e}", encoding="utf-8")
                        
                        # 如果不是最后一次尝试，继续重试
                        if attempt < max_retries - 1:
                            continue
                        else:
                            # 最后一次尝试失败，使用默认值
                            response = RewriteResult(
                                rewrite=False,
                                content=None,
                                summary=text[:497] + "..." if len(text) > 500 else text
                            )
                            break
                            
                except Exception as fallback_e:
                    # 降级调用失败，记录日志
                    (Path(__file__).parent / "summarize_text_fallback_error.log").write_text(f"Fallback call failed (attempt {attempt + 1}): {fallback_e}\nOriginal error: {e}", encoding="utf-8")
                    
                    # 如果不是最后一次尝试，继续重试
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # 最后一次尝试失败，使用默认值
                        response = RewriteResult(
                            rewrite=False,
                            content=None,
                            summary=f"文本摘要生成失败: {text[:300]}..." if len(text) > 300 else text
                        )
                        break
            else:
                # 非JSON错误，如果不是最后一次尝试，继续重试
                if attempt < max_retries - 1:
                    continue
                else:
                    # 最后一次尝试失败，返回默认值
                    print(f"Error invoking LLM after {max_retries} attempts: {e}")
                    return {"raw_text": text, "summary": text[:497] + "...", "url": url}
    else:
        # 如果所有尝试都失败了，返回默认值
        print(f"Failed to summarize text after {max_retries} attempts")
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