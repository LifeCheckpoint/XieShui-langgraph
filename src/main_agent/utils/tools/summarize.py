from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from src.main_agent.llm_manager import llm_manager
from datetime import datetime
from pathlib import Path

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

@tool("note_summarize", args_schema=SummarizeSchema)
def note_summarize(text: str) -> str:
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
        result_text: str = response.content # type: ignore
        title = result_text.split("\n")[0].replace("# ", "")
        title = title if title else f"笔记 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        title += ".md"

        # 保存到文件
        file_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "note_parser" / title
        
        try:
            file_path.write_text(result_text, encoding="utf-8")
        except:
            file_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "note_parser" / f"笔记_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"

            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_path.write_text(result_text, encoding="utf-8")

        return result_text.strip() + f"\n\n笔记已保存到: {file_path.resolve()}"
    
    except Exception as e:
        return f"生成摘要时发生错误: {e}"