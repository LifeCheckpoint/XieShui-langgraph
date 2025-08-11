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
    
    # 最多重试3次
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
            # 记录成功响应用于调试
            (Path(__file__).parent / "generate_outline_success.log").write_text(f"Generate outline response (attempt {attempt + 1}): {response}\nPrompt: {rendered_prompt}", encoding="utf-8")
            break
        except Exception as e:
            # 详细错误记录
            error_details = f"Error generating outline (attempt {attempt + 1}): {e}\nError type: {type(e).__name__}\nPrompt: {rendered_prompt}"
            (Path(__file__).parent / "generate_outline_error.log").write_text(error_details, encoding="utf-8")
            
            # 对于JSON解析错误，尝试手动解析
            if "expected value at line 1 column 1" in str(e) or "json" in str(e).lower() or "validation error" in str(e).lower():
                try:
                    # 降级到非结构化输出进行手动解析
                    fallback_llm = llm_manager.get_llm(config_name="default")
                    fallback_prompt = f"{rendered_prompt}\n\n请严格按照以下JSON格式回复，不要包含任何其他文字:\n{{\n  \"title\": \"报告标题\",\n  \"abstract\": \"报告摘要\",\n  \"outline\": [\n    {{\n      \"title\": \"章节标题\",\n      \"description\": \"章节描述\"\n    }}\n  ]\n}}"
                    
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
                        if "title" not in parsed_content:
                            parsed_content["title"] = f"关于'{state['topic']}'的研究报告"
                        if "abstract" not in parsed_content:
                            parsed_content["abstract"] = f"本报告对'{state['topic']}'进行了深入研究和分析。"
                        if "outline" not in parsed_content:
                            parsed_content["outline"] = [
                                {"title": "引言", "description": "研究背景和目标"},
                                {"title": "研究方法", "description": "采用的研究方法和技术"},
                                {"title": "研究结果", "description": "主要发现和结果"},
                                {"title": "结论", "description": "研究总结和建议"}
                            ]
                        
                        response = Outline(**parsed_content)
                        
                        # 记录手动解析成功
                        (Path(__file__).parent / "generate_outline_manual_success.log").write_text(f"Manual parse successful (attempt {attempt + 1}): {response}\nOriginal error: {e}", encoding="utf-8")
                        break
                        
                    except (json.JSONDecodeError, Exception) as parse_e:
                        # 手动解析失败，记录日志
                        (Path(__file__).parent / "generate_outline_manual_error.log").write_text(f"Manual parse failed (attempt {attempt + 1}): {parse_e}\nFallback content: {fallback_response.content}\nOriginal error: {e}", encoding="utf-8")
                        
                        # 如果不是最后一次尝试，继续重试
                        if attempt < max_retries - 1:
                            continue
                        else:
                            # 最后一次尝试失败，使用默认值
                            response = Outline(
                                title=f"关于'{state['topic']}'的深度研究报告",
                                abstract=f"本报告针对'{state['topic']}'进行了全面的研究和分析，涵盖了相关的理论基础、研究方法、主要发现和结论建议。",
                                outline=[
                                    {"title": "研究背景", "description": "介绍研究领域的背景和重要性"},
                                    {"title": "文献综述", "description": "相关研究的回顾和分析"},
                                    {"title": "研究发现", "description": "主要研究结果和发现"},
                                    {"title": "讨论与结论", "description": "结果讨论和研究结论"}
                                ]
                            )
                            break
                            
                except Exception as fallback_e:
                    # 降级调用失败，记录日志
                    (Path(__file__).parent / "generate_outline_fallback_error.log").write_text(f"Fallback call failed (attempt {attempt + 1}): {fallback_e}\nOriginal error: {e}", encoding="utf-8")
                    
                    # 如果不是最后一次尝试，继续重试
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # 最后一次尝试失败，使用默认值
                        response = Outline(
                            title=f"'{state['topic']}'研究综述",
                            abstract=f"本综述对'{state['topic']}'相关内容进行了系统性的研究和总结。",
                            outline=[
                                {"title": "概述", "description": "主题的基本概念和定义"},
                                {"title": "主要内容", "description": "核心内容和关键要点"},
                                {"title": "总结", "description": "研究总结和展望"}
                            ]
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
        raise Exception(f"Failed to generate outline after {max_retries} attempts")
    
    return {"report_outline": response.model_dump() if hasattr(response, 'model_dump') else response.__dict__, "citations": cite_mapping}

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
    llm = llm_manager.get_llm(config_name="default_moretoken")
    response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])

    def make_valid_filename(filename):
        invalid_chars = ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.']
        valid_filename = ''
        for char in filename:
            if char not in invalid_chars:
                valid_filename += char
            else:
                valid_filename += '_'
        return valid_filename

    text: str = response.content # type: ignore
    title = text.split("\n")[0].strip("# ").strip()
    title = title if title else f"深度研究综述报告 {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
    title = make_valid_filename(title) + ".md"

    # 写入报告到当前目录
    report_path = Path(__file__).parent.parent.parent.parent / "data" / "deep_research" / title
    report_path.write_text(text, encoding="utf-8")
    
    return {"report": text}
