# XieShui-langgraph

## 安装方式

1. 安装 `uv`

    ```shell
    pip install uv
    uv --version
    ```

2. 安装 `LangGraph-CLI` 与 `XieShui` 的 `LangGraph` 核心服务依赖

    ```shell
    uv sync --extra dev
    ```

3. 配置 `LangSmith` 服务监控
    - 复制 `.env.example` 为 `.env`
    - 替换其中内容为：

        ```env
        # To separate your traces from other application
        LANGSMITH_PROJECT=XieShui

        # Add API keys for connecting to LLM providers, data sources, and other integrations here
        LANGSMITH_API_KEY=<key...>
        
        # Tavily
        TAVILY_API_KEY=<key...>
        ```

4. 进入 `src/main_agent` 目录，创建文件 `api_key.json`，并填入 OpenRouter 的 APIKEY

    ```json
    {
        "deepseek/deepseek-chat-v3-0324": "sk-or-v1-xxx",
        "google/gemini-2.5-flash": "sk-or-v1-yyy"
    }
    ```

## 启动项目服务器

```shell
uv run langgraph dev --allow-blocking
```

浏览器将打开 `LangGraph Studio`

## 运行方式

直接点击中间下方的 `Submit` 按钮启动 Agent 图，每次中断都可以与 Agent 进行交互
