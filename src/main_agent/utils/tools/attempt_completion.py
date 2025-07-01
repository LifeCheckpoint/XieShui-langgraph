from pydantic import BaseModel, Field
from langchain_core.tools import tool

class AttemptCompletionSchema(BaseModel):
    """
    当你认为一个任务完成的时候，使用此工具向系统确认该次任务完成

    Example:

    1. 已经成功解答了用户的问题
    - status: 解答完成
    - reason: 通过查询知识库和互联网，成功找到并提供了亚特兰蒂斯的地理信息与相关历史背景，同时更新了用户的知识库

    2. 由于某些原因导致任务失败
    - status: 任务失败
    - reason: 由于网络问题，无法访问相关资源，已向用户说明情况并建议稍后重试
    """
    status: str = Field(description="任务完成状态，例如“成功”或“失败”，保持简短")
    reason: str = Field(description="任务完成情况描述，描述该任务通过什么方式被完成，最终结果是什么")

@tool("attempt_completion", args_schema=AttemptCompletionSchema)
def attempt_completion(status: str, reason: str) -> str:
    return f"任务状态: {status}\n\n完成情况: {reason}"
