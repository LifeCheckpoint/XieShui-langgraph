from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
import json
import jinja2
from aiopath import AsyncPath
import datetime

from src.main_agent.llm_manager import llm_manager

class AnalyzeAndLinkMistakeSchema(BaseModel):
    """
    分析错题描述，提取知识点，并将其关联到知识图谱中。

    这个工具将生成一个“任务书”，调用成功后使用 graph_manager 工具来进行相应知识图谱的补充
    """
    mistake_description: str = Field(description="学生的错题描述。")

@tool("analyze_and_link_mistake", args_schema=AnalyzeAndLinkMistakeSchema)
async def analyze_and_link_mistake(mistake_description: str) -> str:
    """
    分析错题描述，提取知识点，并将其关联到知识图谱中。
    """
    # 1. 读取并渲染 Prompt
    try:
        prompt_path = AsyncPath(__file__).parent / "prompts" / "analyze_and_link_mistake.txt"
        prompt_template_str = await prompt_path.read_text(encoding="utf-8")
        template = jinja2.Template(prompt_template_str)
        rendered_prompt = template.render({"mistake_description": mistake_description})
    except Exception as e:
        return f"读取或渲染 Prompt 模板失败: {e}"

    # 2. 调用 LLM 提取知识点
    llm = llm_manager.get_llm(config_name="default")
    response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])

    if not isinstance(response.content, str):
        return f"LLM 返回了非预期的内容格式: {type(response.content)}"

    try:
        extracted_data = json.loads(response.content)
        keywords = extracted_data.get("keywords", [])
    except (json.JSONDecodeError, AttributeError) as e:
        return f"解析 LLM 返回的 JSON 数据失败: {e}\nLLM原始返回: {response.content}"

    if not keywords:
        return "未能从错题描述中提取出有效的知识点。"

    # 3. 构建 task_book
    task_book_lines = []
    task_book_lines.append(f"1. 切换或创建相关图谱。")
    
    mistake_node_title = f"错题-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    task_book_lines.append(f"2. 使用 add_node 工具创建一个新节点，title 为 '{mistake_node_title}'，description 为 '{mistake_description}'，tags 为 ['错题']。")

    for i, keyword in enumerate(keywords):
        task_book_lines.append(f"{i+3}. 使用 search_nodes_by_keyword 工具搜索关键词 '{keyword}' 相关节点，并进行相应处理。")

    task_book = "\n".join(task_book_lines)

    # 4. 返回给主 Agent 的信息
    return f"任务已生成，下一步必须调用 graph_manager 工具来进行相应知识图谱的补充: \n{task_book}"