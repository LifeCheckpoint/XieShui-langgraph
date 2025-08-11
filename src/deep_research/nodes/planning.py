from __future__ import annotations

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from aiopath import AsyncPath
from pathlib import Path
import jinja2

from src.deep_research.utils.state import MainAgentState
from src.main_agent.llm_manager import llm_manager

# --- Research Plan ---

class ResearchPlan(BaseModel):
    research_status: str = Field(..., description="研究现状。例: 无，我即将开始研究（仅轮次为1时，不允许产生任何已研究幻觉）/ 我已经完成了关于…的研究，但是在…领域存在空白，并且尚未进行关于…的研究 / …")
    research_goal: str = Field(..., description="研究目标。例: 深入探讨QML算法的广度及其未来的发展方向")
    research_range: str = Field(..., description="研究范围。例: 我正在着手对量子机器学习（QML）的理论领域进行全面回顾，重点关注过去8到10年（2015-2025）的研究进展")
    research_method: str = Field(..., description="研究方法。例: 我将首先从…入手，通过…，特别是针对…，来…。我计划涵盖…等。此外，我还会…。我还会收集…，最终将所有收集到的信息综合成一份全面的综述")

async def plan_research(state: MainAgentState) -> dict:
    """根据当前状态制定研究计划"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "research_plan.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    
    template = jinja2.Template(prompt_template_str)

    # 由于会爆 token，所以自适应裁剪所有的 findings

    adapted_state = state.copy()
    # 统计所有 fidings 的总长度
    total_finding_count = sum(len(cycle.get("findings", [])) for cycle in adapted_state["research_cycles"])
    total_finding_length = sum(len(finding) for cycle in adapted_state["research_cycles"] for finding in cycle.get("findings", []))
    # 总长度超过 128000 时，强制裁剪到 100000 // total_finding_count
    if total_finding_length > 128000 and total_finding_count > 0:
        max_finding_length = 100000 // total_finding_count
        for i, cycle in enumerate(adapted_state["research_cycles"]):
            for j, finding in enumerate(cycle.get("findings", [])):
                if len(finding) > max_finding_length:
                    adapted_state["research_cycles"][i]["findings"][j] = finding[:max_finding_length] + "..."
    
    # 渲染模板

    rendered_prompt = template.render({
        "topic": adapted_state["topic"],
        "research_cycles": adapted_state["research_cycles"],
        "research_total_cycles": adapted_state.get("research_total_cycles", 5),
        "current_cycle_index": len(adapted_state["research_cycles"]) + 1
    })
    
    llm = llm_manager.get_llm(config_name="default").with_structured_output(ResearchPlan)
    
    # 最多重试3次
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
            # 记录成功响应用于调试
            (Path(__file__).parent / "success.log").write_text(f"LLM Response (attempt {attempt + 1}): {response}\nPrompt: {rendered_prompt}", encoding="utf-8")
            break
        except Exception as e:
            # 详细错误记录
            error_details = f"Error invoking LLM (attempt {attempt + 1}): {e}\nError type: {type(e).__name__}\nPrompt: {rendered_prompt}"
            (Path(__file__).parent / "error.log").write_text(error_details, encoding="utf-8")
            
            # 对于JSON解析错误，尝试手动解析
            if "expected value at line 1 column 1" in str(e) or "json" in str(e).lower():
                try:
                    # 降级到非结构化输出进行手动解析
                    fallback_llm = llm_manager.get_llm(config_name="default")
                    fallback_prompt = f"{rendered_prompt}\n\n请严格按照以下JSON格式回复，不要包含任何其他文字:\n{{\n  \"research_status\": \"研究现状描述\",\n  \"research_goal\": \"研究目标描述\",\n  \"research_range\": \"研究范围描述\",\n  \"research_method\": \"研究方法描述\"\n}}"
                    
                    fallback_response = await fallback_llm.ainvoke([HumanMessage(content=fallback_prompt)])
                    
                    # 尝试手动解析JSON
                    import json
                    try:
                        content = fallback_response.content.strip()
                        # 移除可能的markdown代码块标记
                        if content.startswith("```json"):
                            content = content[7:]
                        if content.endswith("```"):
                            content = content[:-3]
                        content = content.strip()
                        
                        parsed_content = json.loads(content)
                        response = ResearchPlan(**parsed_content)
                        
                        # 记录手动解析成功
                        (Path(__file__).parent / "manual_parse_success.log").write_text(f"Manual parse successful (attempt {attempt + 1}): {response}\nOriginal error: {e}", encoding="utf-8")
                        break
                        
                    except (json.JSONDecodeError, Exception) as parse_e:
                        # 手动解析失败，记录日志
                        (Path(__file__).parent / "manual_parse_error.log").write_text(f"Manual parse failed (attempt {attempt + 1}): {parse_e}\nFallback content: {fallback_response.content}\nOriginal error: {e}", encoding="utf-8")
                        
                        # 如果不是最后一次尝试，继续重试
                        if attempt < max_retries - 1:
                            continue
                        else:
                            # 最后一次尝试失败，抛出原始异常
                            raise e
                            
                except Exception as fallback_e:
                    # 降级调用失败，记录日志
                    (Path(__file__).parent / "fallback_call_error.log").write_text(f"Fallback call failed (attempt {attempt + 1}): {fallback_e}\nOriginal error: {e}", encoding="utf-8")
                    
                    # 如果不是最后一次尝试，继续重试
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # 最后一次尝试失败，抛出原始异常
                        raise e
            else:
                # 非JSON错误，如果不是最后一次尝试，继续重试
                if attempt < max_retries - 1:
                    continue
                else:
                    # 最后一次尝试失败，抛出异常
                    raise e
    else:
        # 如果所有尝试都失败了，抛出最后一个异常
        raise Exception(f"Failed to get valid response after {max_retries} attempts")
    
    current_cycle = state["research_cycles"][-1]
    current_cycle["research_plan"] = response.dict()
    
    return {"research_cycles": state["research_cycles"]}

# --- Search Queries ---

class SearchQuery(BaseModel):
    content: str = Field(..., description="要搜索的内容")
    reason: str = Field(..., description="进行此搜索的原因")
    max_result: int = Field(..., description="期望的最大结果数")

class SearchQueries(BaseModel):
    queries: list[SearchQuery]

async def generate_search_queries(state: MainAgentState) -> dict:
    """根据研究计划生成搜索查询"""
    prompt_path = AsyncPath(__file__).parent.parent / "utils" / "nodes" / "search_instruction.txt"
    prompt_template_str = await prompt_path.read_text(encoding="utf-8")
    
    template = jinja2.Template(prompt_template_str)
    
    current_cycle = state["research_cycles"][-1]
    
    rendered_prompt = template.render({
        "topic": state["topic"],
        "research_plan": current_cycle["research_plan"]
    })
    
    llm = llm_manager.get_llm(config_name="default").with_structured_output(SearchQueries)
    
    # 最多重试3次
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
            # 记录成功响应用于调试
            (Path(__file__).parent / "search_queries_success.log").write_text(f"Search queries response (attempt {attempt + 1}): {response}\nPrompt: {rendered_prompt}", encoding="utf-8")
            break
        except Exception as e:
            # 详细错误记录
            error_details = f"Error generating search queries (attempt {attempt + 1}): {e}\nError type: {type(e).__name__}\nPrompt: {rendered_prompt}"
            (Path(__file__).parent / "search_queries_error.log").write_text(error_details, encoding="utf-8")
            
            # 对于Pydantic验证错误，尝试手动解析
            if "validation error" in str(e).lower() or "input should be an object" in str(e).lower() or "model_type" in str(e).lower():
                try:
                    # 降级到非结构化输出进行手动解析
                    fallback_llm = llm_manager.get_llm(config_name="default")
                    fallback_prompt = f"{rendered_prompt}\n\n请严格按照以下JSON格式回复，不要包含任何其他文字:\n{{\n  \"queries\": [\n    {{\n      \"content\": \"搜索内容\",\n      \"reason\": \"搜索原因\",\n      \"max_result\": 5\n    }}\n  ]\n}}"
                    
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
                        
                        # 检查是否直接返回了列表而不是对象
                        if isinstance(parsed_content, list):
                            # 包装成期望的格式
                            parsed_content = {"queries": parsed_content}
                        
                        # 确保每个查询都有必需的字段
                        for query in parsed_content.get("queries", []):
                            if "reason" not in query:
                                query["reason"] = f"为了研究'{state['topic']}'相关内容"
                            if "max_result" not in query:
                                query["max_result"] = 5
                        
                        response = SearchQueries(**parsed_content)
                        
                        # 记录手动解析成功
                        (Path(__file__).parent / "search_queries_manual_success.log").write_text(f"Manual parse successful (attempt {attempt + 1}): {response}\nOriginal error: {e}", encoding="utf-8")
                        break
                        
                    except (json.JSONDecodeError, Exception) as parse_e:
                        # 手动解析失败，记录日志
                        (Path(__file__).parent / "search_queries_manual_error.log").write_text(f"Manual parse failed (attempt {attempt + 1}): {parse_e}\nFallback content: {fallback_response.content}\nOriginal error: {e}", encoding="utf-8")
                        
                        # 如果不是最后一次尝试，继续重试
                        if attempt < max_retries - 1:
                            continue
                        else:
                            # 最后一次尝试失败，使用默认值
                            response = SearchQueries(queries=[
                                SearchQuery(
                                    content=f"'{state['topic']}' 基本概念和原理",
                                    reason=f"了解{state['topic']}的基础理论",
                                    max_result=5
                                ),
                                SearchQuery(
                                    content=f"'{state['topic']}' 最新研究进展",
                                    reason=f"获取{state['topic']}的最新发展",
                                    max_result=5
                                )
                            ])
                            break
                            
                except Exception as fallback_e:
                    # 降级调用失败，记录日志
                    (Path(__file__).parent / "search_queries_fallback_error.log").write_text(f"Fallback call failed (attempt {attempt + 1}): {fallback_e}\nOriginal error: {e}", encoding="utf-8")
                    
                    # 如果不是最后一次尝试，继续重试
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # 最后一次尝试失败，使用默认值
                        response = SearchQueries(queries=[
                            SearchQuery(
                                content=f"'{state['topic']}' 综述和概述",
                                reason=f"全面了解{state['topic']}领域",
                                max_result=5
                            )
                        ])
                        break
            else:
                # 非验证错误，如果不是最后一次尝试，继续重试
                if attempt < max_retries - 1:
                    continue
                else:
                    # 最后一次尝试失败，抛出异常
                    raise e
    else:
        # 如果所有尝试都失败了，抛出最后一个异常
        raise Exception(f"Failed to generate search queries after {max_retries} attempts")
    
    current_cycle["search_queries"] = [q.model_dump() for q in response.queries]
    
    return {"research_cycles": state["research_cycles"]}