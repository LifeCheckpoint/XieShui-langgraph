from __future__ import annotations

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from aiopath import AsyncPath
from pathlib import Path
import jinja2
import datetime

from src.deep_research.utils.state import MainAgentState
from src.main_agent.llm_manager import llm_manager

# --- Generate Outline ---

class Outline(BaseModel):
    title: str
    abstract: str
    outline: list[dict]

async def generate_outline(state: MainAgentState) -> dict:
    """根据研究主题、搜索查询和资料摘要，生成学术报告大纲"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "outline_writing.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    
    template = jinja2.Template(prompt_template_str)
    
    relative_searching = [q["content"] for cycle in state["research_cycles"] for q in cycle.get("search_queries", [])]
    
    cite_llm_list = []
    cite_mapping = {}
    cite_id_counter = 1
    for cycle in state["research_cycles"]:
        for result in cycle["summary_raw_content"]:
            if not isinstance(result, dict):
                continue
            
            cite_id = f"C{cite_id_counter}"
            cite_summary = result.get("summary", "No summary available.")
            cite_text = result.get("raw_text", "No raw content available.")
            cite_url = result.get("url", "No URL available.")

            cite_llm_list.append({"cite_id": cite_id, "summary": cite_summary})
            cite_mapping[cite_id] = {
                "summary": cite_summary,
                "text": cite_text,
                "url": cite_url
            }
            cite_id_counter += 1

    rendered_prompt = template.render({
        "subject": state["topic"],
        "relative_searching": relative_searching,
        "cites": cite_llm_list
    })
    
    llm = llm_manager.get_llm(config_name="default").with_structured_output(Outline)
    
    response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
    
    return {"report_outline": response.dict(), "citations": cite_mapping}

# --- Write Sections ---

async def write_sections(state: MainAgentState) -> dict:
    """遍历生成的大纲，逐个章节或小节地撰写报告内容"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "section_writing.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    template = jinja2.Template(prompt_template_str)

    citations = state.get("citations", {})
    report = state.get("report_outline", {}).get("title", "综述报告") + "\n\n"

    async def process_section(section: dict, last_written_content: str, depth: int = 0):
        nonlocal report
        current_section_title = section["title"]

        cites = []        
        # 如果当前章节有引用文献，则添加到 cites 列表
        if "cites" in section:
            for cite_id in section["cites"]:
                if cite_id in citations:
                    cites.append({
                        "cite_id": cite_id,
                        "summary": citations[cite_id]["summary"],
                        "text": citations[cite_id]["text"]
                    })
        
        rendered_prompt = template.render({
            "current_section_title": current_section_title,
            "last_written_content": last_written_content,
            "cites": cites
        })
        
        llm = llm_manager.get_llm(config_name="long_writing")
        response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
        
        report = report + (depth + 2) * "#" + f" {current_section_title}\n\n{response.content}\n\n"
        
        if "sub" in section:
            for sub_section in section["sub"]:
                await process_section(sub_section, report[-500:], depth + 1)

    outline = state.get("report_outline", {}).get("outline", [])
    for section in outline:
        await process_section(section, report[-500:])
    
    # 最后添加引用文献列表
    report += "\n## 参考文献\n\n"
    for cite in citations.items():
        report += f"- {cite[0]}: {cite[1]['url']}\n"
    report += "\n"

    return {"report": report}

# --- Finetune Report ---

async def finetune_report(state: MainAgentState) -> dict:
    """对生成的报告初稿进行整体调优"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "finetune.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    template = jinja2.Template(prompt_template_str)
    rendered_prompt = template.render({"article": state["report"]})
    llm = llm_manager.get_llm(config_name="long_writing")
    response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])

    text: str = response.content # type: ignore
    title = text.split("\n")[0].strip("# ").strip()
    title = title if title else f"深度研究综述报告 {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
    title = title + ".md"

    # 写入报告到当前目录
    report_path = Path(__file__).parent.parent.parent.parent / "data" / "deep_research" / title
    report_path.write_text(text, encoding="utf-8")
    
    return {"report": text}
