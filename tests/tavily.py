from langchain_tavily import TavilySearch

web_search = TavilySearch(
    tavily_api_key="",
    max_results=5,
)

search_prompt = """
你将进行网络资料检索。检索信息如下

- **检索内容**：use the LangGraph SDK create agent
- **检索原因**：了解LangGraph SDK创建Agent的最佳实践与方法，以形成对构建智能体方法论的初步了解

完成检索后，请将源与参考资料尽可能详细列出
"""

web_search_results = web_search.invoke("use the LangGraph SDK create agent")

print(web_search_results["results"])