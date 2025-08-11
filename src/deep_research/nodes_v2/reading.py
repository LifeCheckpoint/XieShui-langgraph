"""
Deep Research Reading 节点 - 重构版本
使用新的服务抽象层，保持智能转写功能
"""

from __future__ import annotations

import asyncio
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from src.deep_research.utils.state import MainAgentState
from src.deep_research.services.llm_service import llm_service
from src.deep_research.services.state_manager import state_manager
from src.deep_research.services.config_manager import config_manager


class RewriteResult(BaseModel):
    rewrite: bool = Field(..., description="是否需要转写")
    content: str | None = Field(None, description="转写后的内容")
    summary: str = Field(..., description="对文本的简短摘要")


async def read_and_summarize(state: MainAgentState) -> dict:
    """
    读取并总结精读和略读列表中的所有网页
    
    重构后的实现：
    - 保持完全相同的智能转写和摘要逻辑
    - 使用配置管理器控制内容长度限制
    - 使用统一的错误处理和重试机制
    """
    # 验证状态转换
    state_manager.validate_transition_to(state, "read_and_summarize")
    
    # 获取当前循环数据
    current_cycle = state_manager.get_current_cycle(state)
    reading_list = current_cycle.get("reading_list", [])
    skimming_list = current_cycle.get("skimming_list", [])
    search_results = current_cycle.get("search_results", [])
    
    topic = state["topic"]
    research_plan = current_cycle.get("research_plan", {})
    
    # 创建URL到raw_content的映射（用于精读）
    raw_content_map = {
        res["url"]: res["raw_content"] 
        for res in search_results 
        if res.get("raw_content")
    }
    
    # 准备所有读取任务
    tasks = []
    
    # 处理精读列表
    for url in reading_list:
        if url in raw_content_map:
            # 使用已有的raw_content进行智能转写
            tasks.append(_summarize_text_with_rewrite(
                raw_content_map[url], topic, research_plan, url
            ))
        else:
            # 需要重新获取内容
            tasks.append(_read_and_summarize_page(url, topic, research_plan))
    
    # 处理略读列表
    for url in skimming_list:
        tasks.append(_read_and_summarize_page(url, topic, research_plan))
    
    # 并发执行所有读取任务
    summaries = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 过滤掉异常结果，保留有效摘要
    valid_summaries = []
    summary_raw_content = []
    
    for summary in summaries:
        if isinstance(summary, Exception):
            # 记录异常但不中断流程
            print(f"Reading task failed: {summary}")
            summary_raw_content.append(f"Error: {str(summary)}")
        elif isinstance(summary, dict) and "summary" in summary:
            valid_summaries.append(summary)
            summary_raw_content.append(summary)
        else:
            summary_raw_content.append(str(summary))
    
    # 使用状态管理器更新发现
    return state_manager.update_findings(state, valid_summaries, summary_raw_content)


async def _summarize_text_with_rewrite(
    text: str, 
    topic: str, 
    research_plan: dict, 
    url: str
) -> dict:
    """
    对给定文本进行智能转写和摘要
    
    重构后的实现：
    - 移除了100+行的重复错误处理代码
    - 使用统一的LLM服务进行转写判断
    - 保持完全相同的转写逻辑和质量标准
    """
    try:
        # 应用内容长度限制
        max_length = config_manager.research.content_max_length
        if len(text) > max_length:
            half_length = max_length // 2
            text = text[:half_length] + "..." + text[-half_length:]
        
        # 准备模板上下文
        context = {
            "topic": topic,
            "research_plan": research_plan,
            "original_text": text
        }
        
        # 使用LLM服务进行智能转写判断
        llm_config = config_manager.get_llm_config_for_task("reading")
        response = await llm_service.invoke_with_template(
            "rewrite.txt",
            context,
            RewriteResult,
            llm_config
        )
        
        # 安全地提取结果
        if hasattr(response, 'rewrite'):
            rewrite = response.rewrite  # type: ignore
            content = response.content  # type: ignore
            summary = response.summary  # type: ignore
        else:
            # 转换为字典进行安全访问
            result_dict = response.model_dump() if hasattr(response, 'model_dump') else {}
            rewrite = result_dict.get("rewrite", False) if isinstance(result_dict, dict) else False
            content = result_dict.get("content") if isinstance(result_dict, dict) else None
            summary = result_dict.get("summary", text[:200] + "...") if isinstance(result_dict, dict) else text[:200] + "..."
        
        # 构建返回结果
        return {
            "raw_text": content if rewrite and content else text,
            "summary": summary,
            "url": url,
            "rewritten": rewrite
        }
        
    except Exception as e:
        # 降级处理：返回原始文本的摘要
        print(f"Rewrite failed for {url}: {e}")
        return {
            "raw_text": text,
            "summary": text[:200] + "..." if len(text) > 200 else text,
            "url": url,
            "rewritten": False,
            "error": str(e)
        }


async def _read_and_summarize_page(url: str, topic: str, research_plan: dict) -> dict:
    """
    读取单个网页并进行总结
    
    重构后的实现：
    - 保持完全相同的网页读取和解析逻辑
    - 使用配置管理器控制超时参数
    - 统一的错误处理
    """
    try:
        # 使用配置中的超时设置
        timeout = config_manager.get_search_config()["timeout"]
        
        # 获取网页内容
        response = await asyncio.to_thread(
            requests.get, 
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}, 
            timeout=timeout
        )
        response.raise_for_status()
        
        # 解析HTML内容
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 清理脚本和样式标签
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 提取纯文本
        original_text = soup.get_text(separator='\n', strip=True)
        
        # 进行智能转写和摘要
        return await _summarize_text_with_rewrite(original_text, topic, research_plan, url)
        
    except Exception as e:
        return {
            "raw_text": "",
            "summary": f"Error reading {url}: {str(e)}",
            "url": url,
            "rewritten": False,
            "error": str(e)
        }


# 为了向后兼容，提供原有接口的包装函数
async def summarize_text_legacy(text: str, topic: str, research_plan: dict, url: str) -> dict:
    """向后兼容的文本摘要函数"""
    return await _summarize_text_with_rewrite(text, topic, research_plan, url)


async def read_and_summarize_page_legacy(url: str, topic: str, research_plan: dict) -> dict:
    """向后兼容的网页读取函数"""
    return await _read_and_summarize_page(url, topic, research_plan)


def _validate_reading_input(reading_list: list, skimming_list: list) -> bool:
    """验证读取输入的有效性"""
    if not isinstance(reading_list, list) or not isinstance(skimming_list, list):
        return False
    
    # 检查URL格式的基本有效性
    for url_list in [reading_list, skimming_list]:
        for url in url_list:
            if not isinstance(url, str) or not url.strip():
                return False
            if not (url.startswith('http://') or url.startswith('https://')):
                return False
    
    return True


def _calculate_reading_priority(url: str, title: str = "") -> int:
    """计算读取优先级（用于未来的优化）"""
    priority = 0
    
    # 基于URL特征的优先级
    if any(domain in url.lower() for domain in ["arxiv", "nature", "science", "ieee"]):
        priority += 10  # 学术源优先级高
    
    if any(domain in url.lower() for domain in ["wikipedia", "github"]):
        priority += 5   # 技术文档优先级中等
    
    # 基于标题特征的优先级
    if title:
        academic_keywords = ["research", "analysis", "study", "paper", "journal"]
        if any(keyword in title.lower() for keyword in academic_keywords):
            priority += 5
    
    return priority