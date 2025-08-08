from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
import json
import jinja2
from aiopath import AsyncPath

from src.main_agent.llm_manager import llm_manager

class AnswerWithGraphPathSchema(BaseModel):
    """
    分析用户问题，在知识图谱中寻找相关路径或子图，并基于此生成可解释的答案。
    """
    question: str = Field(description="用户提出的问题。")
    graph_name: str = Field(description="当前使用的知识图谱名称。")

@tool("answer_with_graph_path", args_schema=AnswerWithGraphPathSchema)
async def answer_with_graph_path(question: str, graph_name: str) -> str:
    """
    分析用户问题，在知识图谱中寻找相关路径或子图，并基于此生成可解释的答案。
    """
    # 1. 提取实体
    try:
        prompt_path = AsyncPath(__file__).parent / "prompts" / "answer_with_graph_path_entity_extraction.txt"
        prompt_template_str = await prompt_path.read_text(encoding="utf-8")
        template = jinja2.Template(prompt_template_str)
        rendered_prompt = template.render({"question": question})
    except Exception as e:
        return f"读取或渲染实体提取 Prompt 失败: {e}"

    llm_entity_extractor = llm_manager.get_llm(config_name="default")
    response = await llm_entity_extractor.ainvoke([HumanMessage(content=rendered_prompt)])

    if not isinstance(response.content, str):
        return f"LLM (实体提取) 返回了非预期的内容格式: {type(response.content)}"

    try:
        extracted_data = json.loads(response.content)
        entities = extracted_data.get("entities", [])
    except (json.JSONDecodeError, AttributeError) as e:
        return f"解析 LLM (实体提取) 返回的 JSON 数据失败: {e}\nLLM原始返回: {response.content}"

    if not entities:
        return "未能从问题中提取出核心概念，无法在知识图谱中查找。"

    # 2. 构建 task_book
    task_book_lines = [f"1. 切换到名为 '{graph_name}' 的图谱。"]
    
    if len(entities) >= 2:
        # 查找路径
        start_node, end_node = entities[0], entities[1]
        task_book_lines.append(f"2. 使用 search_nodes_by_keyword 找到 '{start_node}' 的节点 ID。")
        task_book_lines.append(f"3. 使用 search_nodes_by_keyword 找到 '{end_node}' 的节点 ID。")
        task_book_lines.append(f"4. 使用 find_path 查找这两个节点之间的路径，并返回路径上所有节点和边的详细信息。")
        # 备用逻辑：如果找不到路径，则获取邻居
        task_book_lines.append(f"5. (如果上一步未找到路径) 使用 get_k_hop_neighborhood (k=1) 分别获取 '{start_node}' 和 '{end_node}' 的邻居节点信息。")
    else:
        # 开放性问题，获取子图
        core_concept = entities[0]
        task_book_lines.append(f"2. 使用 get_k_hop_neighborhood (k=2) 获取 '{core_concept}' 节点的二跳邻居子图信息。")

    task_book = "\n".join(task_book_lines)

    # 3. 调用 graph_manager (模拟)
    # 在真实场景中，main_agent 会调用 graph_manager 子图并获得其返回的图谱信息。
    # 这里我们直接返回 task_book，让主 Agent 去执行。
    # 实际的答案生成步骤应该在主 Agent 收到 graph_manager 的返回结果后进行。
    
    # 为了演示，我们假设已经从 graph_manager 获取了信息
    # graph_info = "这是从 graph_manager 获取的模拟路径/子图信息..."
    # try:
    #     prompt_path_gen = AsyncPath(__file__).parent / "prompts" / "answer_with_graph_path_answer_generation.txt"
    #     prompt_template_str_gen = await prompt_path_gen.read_text(encoding="utf-8")
    #     template_gen = jinja2.Template(prompt_template_str_gen)
    #     rendered_prompt_gen = template_gen.render({"question": question, "graph_info": graph_info})
    # except Exception as e:
    #     return f"读取或渲染答案生成 Prompt 失败: {e}"
    # 
    # llm_answer_generator = llm_manager.get_llm(config_name="long_writing")
    # final_response = await llm_answer_generator.ainvoke([HumanMessage(content=rendered_prompt_gen)])
    # return final_response.content

    return f"任务已生成，准备提交给知识图谱管理器以获取路径/子图信息: \n{task_book}"