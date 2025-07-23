from pydantic import BaseModel, Field
from langchain_core.tools import tool
import json

class KLGraphAbortSchema(BaseModel):
    """
    当你认为知识图谱管理任务未能完成的时候，使用此工具向管理者报告错误，或进一步要求更多信息

    Example:

    1. 由于某些原因导致任务失败
    - status: 任务失败
    - detail: 我在执行计划的第3步，尝试添加节点的时候，系统向我报告了一个错误，提示“节点标题不能为空”。我检查了输入，发现确实已经提供了节点标题，重复尝试后无法解决，因此我决定报告该问题，请系统管理员进行调查和修复。

    2. 信息有错乱，导致知识图谱难以建模
    - status: 信息模糊
    - detail: 我在处理节点“量子计算”时，发现其描述中包含了多个不相关的概念，如“音乐鉴赏”和“文学素养建设”，这使得我无法准确理解该节点的核心内容。建议对该节点进行重新审视和修正，以便更好地进行建模。同时，我注意到该节点的标签与其内容不符，建议将标签“艺术”更改为“科学”，以更准确地反映其主题。

    3. 信息过于模糊或不完整，无法进行建模
    - status: 信息不完整
    - detail: 我在处理节点“量子计算”时，发现其任务书描述中缺乏要建模的信息，仅提供了“量子计算”这个简单的信息，因此我无法进行有效的建模。建议提供更详细的背景信息和相关数据，以便我能够更好地理解该节点的内容和意义。另外，节点标签未提供，建议添加相关标签以便更好地分类和检索。
    """
    status: str = Field(description="任务完成状态")
    detail: str = Field(description="任务完成情况描述，描述该任务通过什么方式被完成，最终结果是什么。如果是报告信息，一定要尽可能详细")

@tool("klgraph_abort", args_schema=KLGraphAbortSchema)
def klgraph_abort(status: str, detail: str) -> str:
    return json.dumps({
        "status": status,
        "detail": detail
    }, ensure_ascii=False, indent=4)