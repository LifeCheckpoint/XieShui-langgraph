from pydantic import BaseModel, Field
from langchain_core.tools import tool

class AttemptCompletionSchema(BaseModel):
    """
    当你认为一个任务完成的时候，使用此工具向系统确认该次任务完成
    """
    status: str = Field(description="任务完成状态，例如“成功”或“失败”，保持简短")
    reason: str = Field(description="任务完成情况描述，描述该任务通过什么方式被完成，最终结果是什么")

@tool("attempt_completion", args_schema=AttemptCompletionSchema)
def attempt_completion(status: str, reason: str) -> str:
    return f"任务状态: {status}\n\n完成情况: {reason}"
