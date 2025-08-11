"""
Deep Research Writing 节点 - 重构版本
使用引用管理服务和LLM服务，大幅简化学术写作逻辑
"""

from __future__ import annotations

import datetime
from pydantic import BaseModel, Field

from src.deep_research.utils.state import MainAgentState
from src.deep_research.services.llm_service import llm_service
from src.deep_research.services.state_manager import state_manager
from src.deep_research.services.citation_service import citation_service
from src.deep_research.services.config_manager import config_manager
from src.deep_research.core.paths import ensure_output_dir, make_valid_filename


class Outline(BaseModel):
    title: str
    abstract: str
    outline: list[dict]


async def generate_outline(state: MainAgentState) -> dict:
    """
    根据研究主题、搜索查询和资料摘要，生成学术报告大纲
    
    重构后的实现：
    - 使用引用管理服务统一处理引用映射
    - 移除了100+行的重复错误处理代码
    - 保持完全相同的大纲生成逻辑和格式
    """
    # 验证状态转换
    state_manager.validate_transition_to(state, "generate_outline")
    
    # 收集所有搜索查询内容
    relative_searching = state_manager.get_all_search_queries(state)
    
    # 收集所有原始内容并创建引用映射
    all_raw_content = []
    for cycle in state["research_cycles"]:
        summary_raw_content = cycle.get("summary_raw_content", [])
        for content in summary_raw_content:
            if isinstance(content, dict):
                all_raw_content.append(content)
    
    # 使用引用服务创建引用映射
    cite_llm_list, cite_mapping = citation_service.create_citation_map(all_raw_content)
    
    # 准备模板上下文
    context = {
        "subject": state["topic"],
        "relative_searching": relative_searching,
        "cites": cite_llm_list
    }
    
    # 使用LLM服务生成大纲
    llm_config = config_manager.get_llm_config_for_task("writing")
    response = await llm_service.invoke_with_template(
        "outline_writing.txt",
        context,
        Outline,
        llm_config
    )
    
    # 提取结果
    if hasattr(response, 'model_dump'):
        outline_dict = response.model_dump()
    else:
        outline_dict = response.__dict__ if hasattr(response, '__dict__') else {}
    
    # 返回大纲和引用映射
    return {
        "report_outline": outline_dict,
        "citations": cite_mapping
    }


async def write_sections(state: MainAgentState) -> dict:
    """
    遍历生成的大纲，逐个章节或小节地撰写报告内容
    
    重构后的实现：
    - 使用引用管理服务处理章节引用
    - 保持完全相同的递归写作逻辑
    - 使用配置管理器控制章节长度
    """
    # 验证状态转换
    state_manager.validate_transition_to(state, "write_sections")
    
    # 获取大纲和引用数据
    citations = state.get("citations", {})
    report_outline = state.get("report_outline", {})
    
    # 初始化报告内容
    report = report_outline.get("title", "综述报告") + "\n\n"
    
    # 递归处理章节的内部函数
    async def process_section(section: dict, last_written_content: str, depth: int = 0):
        nonlocal report
        current_section_title = section["title"]
        
        # 获取当前章节的引用
        section_citations = []
        if "cites" in section:
            section_citations = citation_service.get_citations_for_section(
                section["cites"], citations
            )
        
        # 准备模板上下文
        context = {
            "current_section_title": current_section_title,
            "last_written_content": last_written_content,
            "cites": section_citations
        }
        
        # 使用LLM服务写作章节
        llm_config = config_manager.get_llm_config_for_task("writing")
        section_content = await llm_service.invoke_with_template_simple(
            "section_writing.txt",
            context,
            llm_config
        )
        
        # 添加章节标题和内容
        header_level = "#" * (depth + 2)
        report += f"{header_level} {current_section_title}\n\n{section_content}\n\n"
        
        # 递归处理子章节
        if "sub" in section:
            for sub_section in section["sub"]:
                await process_section(sub_section, report[-500:], depth + 1)
    
    # 处理所有章节
    outline = report_outline.get("outline", [])
    for section in outline:
        await process_section(section, report[-500:])
    
    # 添加参考文献
    bibliography = citation_service.generate_bibliography(citations)
    report += bibliography
    
    return {"report": report}


async def finetune_report(state: MainAgentState) -> dict:
    """
    对生成的报告初稿进行整体调优
    
    重构后的实现：
    - 使用路径工具管理输出文件
    - 保持完全相同的调优逻辑
    - 自动生成有效文件名并保存
    """
    # 验证状态转换
    state_manager.validate_transition_to(state, "finetune_report")
    
    # 准备调优上下文
    context = {"article": state["report"]}
    
    # 使用LLM服务进行报告调优
    llm_config = config_manager.get_llm_config_for_task("finetune")
    refined_content = await llm_service.invoke_with_template_simple(
        "finetune.txt",
        context,
        llm_config
    )
    
    # 提取标题并生成文件名
    title = _extract_title_from_content(refined_content)
    if not title:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"深度研究综述报告 {timestamp}"
    
    # 生成有效文件名
    filename = make_valid_filename(title) + ".md"
    
    # 保存报告到输出目录
    output_dir = ensure_output_dir()
    report_path = output_dir / filename
    
    try:
        report_path.write_text(refined_content, encoding="utf-8")
        print(f"Report saved to: {report_path}")
    except Exception as e:
        print(f"Failed to save report: {e}")
    
    return {"report": refined_content}


def _extract_title_from_content(content: str) -> str:
    """从报告内容中提取标题"""
    try:
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # 第一个非空非标题行作为标题
                return line.strip("# ").strip()
            elif line.startswith("# "):
                # 或者第一个一级标题
                return line.strip("# ").strip()
        return ""
    except Exception:
        return ""


def _validate_outline_structure(outline: dict) -> bool:
    """验证大纲结构的有效性"""
    required_fields = ["title", "abstract", "outline"]
    
    for field in required_fields:
        if field not in outline:
            return False
    
    if not isinstance(outline["outline"], list):
        return False
    
    return True


def _validate_citations_consistency(report: str, citations: dict) -> tuple[bool, list[str]]:
    """验证报告中引用的一致性"""
    return citation_service.validate_citation_references(report, citations)


def _calculate_writing_metrics(report: str) -> dict:
    """计算写作指标"""
    lines = report.split('\n')
    words = len(report.split())
    characters = len(report)
    
    # 统计章节数量
    sections = sum(1 for line in lines if line.strip().startswith('#'))
    
    # 统计引用数量
    citations = len(citation_service.extract_citations_from_text(report))
    
    return {
        "word_count": words,
        "character_count": characters,
        "line_count": len(lines),
        "section_count": sections,
        "citation_count": citations
    }


# 为了向后兼容，提供原有接口的包装函数
async def generate_outline_legacy(
    topic: str, 
    relative_searching: list, 
    cite_llm_list: list
) -> Outline:
    """向后兼容的大纲生成函数"""
    context = {
        "subject": topic,
        "relative_searching": relative_searching,
        "cites": cite_llm_list
    }
    
    response = await llm_service.invoke_with_template(
        "outline_writing.txt",
        context,
        Outline
    )
    
    return response  # type: ignore


async def write_section_legacy(
    section_title: str,
    last_content: str,
    citations: list
) -> str:
    """向后兼容的章节写作函数"""
    context = {
        "current_section_title": section_title,
        "last_written_content": last_content,
        "cites": citations
    }
    
    return await llm_service.invoke_with_template_simple(
        "section_writing.txt",
        context
    )


async def finetune_report_legacy(report_content: str) -> str:
    """向后兼容的报告调优函数"""
    context = {"article": report_content}
    
    return await llm_service.invoke_with_template_simple(
        "finetune.txt",
        context
    )