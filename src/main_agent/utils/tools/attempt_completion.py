from pydantic import BaseModel, Field
from langchain_core.tools import tool

class AttemptCompletionSchema(BaseModel):
    """
    当你认为一个任务完成的时候，使用此工具向系统确认该次任务完成。收到工具使用结果并确认任务已完成后，使用此工具向用户展示您的工作结果。
    如果用户对结果不满意，他们可能会给出反馈，您可以使用反馈进行改进并重试。
    注意，在使用这个工具之前，你需要详细地向用户解释当前任务的执行结果，最后再使用该工具向系统提交完成状态。

    Example:

    1. 已经成功解答了用户的问题
    - status: 解答完成
    - reason: 通过查询知识库和互联网，成功找到并提供了亚特兰蒂斯的地理信息与相关历史背景，同时更新了用户的知识库

    2. 由于某些原因导致任务失败
    - status: 任务失败
    - reason: 由于网络问题，无法访问相关资源，已向用户说明情况并建议稍后重试
    """
    status: str = Field(description="任务完成状态，例如“成功”或“失败”，保持简短")
    reason: str = Field(description="任务完成情况描述，描述该任务通过什么方式被完成，最终结果是什么。另外，不要填写疑问句或“如有更多请求可以向我询问”等句子")

@tool("attempt_completion", args_schema=AttemptCompletionSchema)
def attempt_completion(status: str, reason: str) -> str:
    return f"任务状态: {status}\n\n完成情况: {reason}"
