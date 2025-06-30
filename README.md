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
        ```

## 启动项目服务器

```shell
uv run langgraph dev
```

浏览器将打开 `LangGraph Studio`
