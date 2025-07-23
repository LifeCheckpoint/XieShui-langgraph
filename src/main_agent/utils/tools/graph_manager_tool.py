from pydantic import BaseModel, Field
from langchain_core.tools import tool
import json

class GraphManagerSchema(BaseModel):
    """
    当你需要对知识图谱进行管理、操作、查询或分析时，使用此工具。
    它会调用一个专门的知识图谱管理 Agent 来执行复杂的图谱任务。

    Example:

    1. 用户要求创建一个新的知识图谱来记录“人工智能”领域的知识
    - task_book: "创建一个名为 'AI_Knowledge' 的新知识图谱，并添加一个核心节点 '人工智能'，描述为 '研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学'。"

    2. 用户要求查询现有图谱中关于“机器学习”的信息
    - task_book: "在名为 'AI_Knowledge' 的图谱中，查询所有与 '机器学习' 标签相关的节点，并返回它们的详细信息。"
    """
    task_book: str = Field(description="一份详细的任务书，描述了需要对知识图谱执行的管理任务。请尽可能详细地描述任务目标、涉及的图谱名称、节点/边信息等。")

@tool("graph_manager", args_schema=GraphManagerSchema)
def graph_manager(task_book: str) -> str:
    """
    调用知识图谱管理 Agent (graph_manager) 来执行图谱操作。
    """
    return json.dumps({
        "task_book": task_book
    }, ensure_ascii=False, indent=4)