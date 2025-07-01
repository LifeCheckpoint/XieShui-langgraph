from __future__ import annotations

from langchain_openai import ChatOpenAI
from pathlib import Path
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

llm = ChatOpenAI(
    model="deepseek/deepseek-chat-v3-0324",
    temperature=0.3,
    base_url="https://openrouter.ai/api/v1",
    api_key=(Path(__file__).parent / "api_key").read_text(encoding="utf-8").strip(),
    max_retries=3,
    max_tokens=8192,
    # frequency_penalty=0.4,
)

response = llm.invoke(
    [
        HumanMessage(content="你好，今天的天气怎么样？"),
        AIMessage(content="根据查询结果，北京今天的天气晴朗，最高温度25°C，最低温度15°C。"),
        HumanMessage(content="你是怎么知道的？是"),
        AIMessage(content="我是通过调用天气查询工具获取的最新天气信息。"),
        HumanMessage(content="你能告诉我更多关于这个工具的信息吗？"),
        AIMessage(content="当然，这个工具可以查询指定地点的天气情况，包括温度、湿度等信息。"),
        HumanMessage(content="天气工具的使用方法"),
    ]
)

print(response)