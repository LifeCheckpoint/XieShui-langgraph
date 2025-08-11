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
    """
    import datetime
    from pathlib import Path
    
    # 创建调试日志
    log_file = Path("src/deep_research/logs/debug_write_sections.log")
    log_file.parent.mkdir(exist_ok=True)
    
    def write_log(message: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

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

        try:
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

        except Exception as e:
            write_log(f"Error processing section '{section.get('title', 'Unknown')}' at depth {depth}: {e}")
    
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
    
    return {"report": f"深度研究文件已保存到 {report_path.resolve()}"}


def _extract_title_from_content(content: str) -> str:
    """从报告内容中提取标题"""
    def sym_filter(s: str) -> str:
        for sym in [":", "\\", "/", "*", "?", "\"", "<", ">", "|", "!", "#", "@", "$"]:
            s = s.replace(sym, "")
        return s
    
    try:
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # 第一个非空非标题行作为标题
                return sym_filter(line.strip("# ").strip())
            elif line.startswith("# "):
                # 或者第一个一级标题
                return sym_filter(line.strip("# ").strip())
        return ""
    except Exception:
        return ""
