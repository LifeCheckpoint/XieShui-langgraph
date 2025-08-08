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
    """
    mistake_description: str = Field(description="学生的错题描述。")
    graph_name: str = Field(description="当前学生使用的知识图谱名称。")

@tool("analyze_and_link_mistake", args_schema=AnalyzeAndLinkMistakeSchema)
async def analyze_and_link_mistake(mistake_description: str, graph_name: str) -> str:
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
    task_book_lines.append(f"1. 切换到名为 '{graph_name}' 的图谱。")
    
    mistake_node_title = f"错题-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    task_book_lines.append(f"2. 使用 add_node 工具创建一个新节点，title 为 '{mistake_node_title}'，description 为 '{mistake_description}'，tags 为 ['错题']。")

    for i, keyword in enumerate(keywords):
        task_book_lines.append(f"{i+3}. 使用 search_nodes_by_keyword 工具搜索关键词 '{keyword}'。")
        # 这里的逻辑需要在 graph_manager Agent 中实现：如果搜索不到，则创建新节点。
        # 简化起见，我们假设 graph_manager Agent 能够处理这种情况。
        # 实际实现中，可能需要更复杂的交互或在 task_book 中加入条件逻辑。
        task_book_lines.append(f"{i+3}.1. (如果上一步未找到节点) 使用 add_node 创建一个 title 为 '{keyword}' 的新节点。")
        task_book_lines.append(f"{i+3}.2. 使用 update_node 工具，为 '{keyword}' 节点的 tags 列表添加 '易错点' 标签。")
        task_book_lines.append(f"{i+3}.3. 使用 add_edge 工具，将 '{mistake_node_title}' 节点与 '{keyword}' 节点连接，边的 title 为 '相关错题'。")

    task_book = "\n".join(task_book_lines)

    # 4. 返回给主 Agent 的信息
    return f"任务已生成，准备提交给知识图谱管理器: \n{task_book}"