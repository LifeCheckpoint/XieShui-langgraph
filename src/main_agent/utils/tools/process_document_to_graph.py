from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
import json
import jinja2
from aiopath import AsyncPath

from src.main_agent.llm_manager import llm_manager
# 暂时无法直接调用子图，注释掉
# from src.main_agent.utils.nodes.subgraph import graph_manager_node

class ProcessDocumentToGraphSchema(BaseModel):
    """
    处理单个文档，提取知识点并生成或更新知识图谱。
    """
    file_path: str = Field(description="要处理的讲义文件的路径。")

@tool("process_document_to_graph", args_schema=ProcessDocumentToGraphSchema)
async def process_document_to_graph(file_path: str) -> str:
    """
    处理单个文档，提取知识点并生成或更新知识图谱。
    """
    # 1. 读取文件内容
    try:
        async with AsyncPath(file_path).open('r', encoding='utf-8') as f:
            content = await f.read()
    except Exception as e:
        return f"读取文件失败: {e}"

    # 2. 读取并渲染 Prompt
    try:
        prompt_path = AsyncPath(__file__).parent / "prompts" / "process_document_to_graph.txt"
        prompt_template_str = await prompt_path.read_text(encoding="utf-8")
        template = jinja2.Template(prompt_template_str)
        
        # TODO: 在实际应用中，这里应该调用 graph_manager 的 list_current_graph 工具获取图谱列表
        existing_graphs = [] 
        
        rendered_prompt = template.render({
            "existing_graphs": existing_graphs,
            "content": content
        })
    except Exception as e:
        return f"读取或渲染 Prompt 模板失败: {e}"

    # 3. 调用 LLM 提取节点和边
    llm = llm_manager.get_llm(config_name="default")
    response = await llm.ainvoke([HumanMessage(content=rendered_prompt)])
    
    # 确保 response.content 是字符串
    if not isinstance(response.content, str):
        return f"LLM 返回了非预期的内容格式: {type(response.content)}"

    try:
        extracted_data = json.loads(response.content)
        action = extracted_data.get("action")
        target_graph_name = extracted_data.get("graph_name")
        nodes = extracted_data.get("nodes", [])
        edges = extracted_data.get("edges", [])
    except (json.JSONDecodeError, AttributeError) as e:
        return f"解析 LLM 返回的 JSON 数据失败: {e}\nLLM原始返回: {response.content}"

    if not target_graph_name:
        return "LLM 未能决定目标图谱的名称。"

    # 4. 构建 task_book
    task_book_lines = []
    if action == "create":
        task_book_lines.append(f"1. 使用 add_graph 工具创建一个名为 '{target_graph_name}' 的新图谱。")
    
    task_book_lines.append(f"2. 切换到名为 '{target_graph_name}' 的图谱。")
    
    batch_data = {"nodes": nodes, "edges": edges}
    task_book_lines.append(f"3. 使用 batch_add_from_json 工具批量添加以下节点和边: {json.dumps(batch_data, ensure_ascii=False)}")

    task_book = "\n".join(task_book_lines)

    # 5. 返回给主 Agent 的信息
    # 主 Agent 将根据这个 task_book 调用 graph_manager 子图
    return f"任务已生成，准备提交给知识图谱管理器: \n{task_book}"