from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from pathlib import Path
from src.main_agent.llm_manager import llm_manager

class SummarizeSchema(BaseModel):
    """
    当你需要对一段长文本（如学术资料、课程讲义等）进行高质量的总结和笔记整理时，使用此工具。
    它会根据预设的专业指令来生成结构化、重点突出、易于理解的笔记。

    Example:
    - text: "这里是一段关于人工智能历史的详细文本..."
    """
    text: str = Field(description="需要总结和整理的原始文本内容。")

# 加载指令
try:
    instruction_path = Path(__file__).parent / "summary.txt"
    instruction = instruction_path.read_text(encoding="utf-8")
except FileNotFoundError:
    instruction = "请为我总结以下文本。"

@tool("summarize", args_schema=SummarizeSchema)
def summarize(text: str) -> str:
    """
    根据专业指令对文本进行总结和笔记整理。
    """
    try:
        # 获取 LLM 实例
        llm = llm_manager.get_llm("default")
        
        # 构建消息
        messages = [
            SystemMessage(content=instruction),
            HumanMessage(content=text),
        ]
        
        # 调用 LLM
        response = llm.invoke(messages)
        
        return response.content # type: ignore
    except Exception as e:
        return f"生成摘要时发生错误: {e}"