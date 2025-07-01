# LLM 管理

XieShui Agent 通过 `LLMManager` 类来统一管理和实例化不同配置的语言模型（LLM）。这种设计使得 Agent 能够根据不同的任务需求灵活地选择和使用合适的 LLM，同时方便了模型配置的集中管理。

## `LLMConfig`：LLM 配置模型

`LLMConfig` 定义了单个 LLM 实例的配置参数。它是一个基于 Pydantic `BaseModel` 的数据结构，确保了配置的类型安全。

`LLMConfig` 定义在 [`src/main_agent/llm_manager.py`](src/main_agent/llm_manager.py) 中，其结构如下：

```python
from typing import Any, Dict, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import json

class LLMConfig(BaseModel):
    """
    LLM 配置模型
    """
    model_name: str = Field(default="deepseek/deepseek-chat-v3-0324", description="LLM 模型名称")
    temperature: float = Field(default=0.3, description="LLM 温度")
    base_url: str = Field(default="https://openrouter.ai/api/v1", description="LLM API Base URL")
    max_retries: int = Field(default=3, description="LLM 最大重试次数")
    max_tokens: int = Field(default=8192, description="LLM 最大 token 数")
    frequency_penalty: float = Field(default=0.0, description="LLM 频率惩罚")
    api_key_path: str = Field(default=(Path(__file__).parent / "api_key.json").as_posix(), description="API Key 文件路径")

    def get_api_key(self) -> Optional[str]:
        json_text = Path(self.api_key_path).read_text(encoding="utf-8").strip()
        return json.loads(json_text).get(self.model_name)
```

### 字段说明

* **`model_name`**: LLM 的模型名称，例如 `"deepseek/deepseek-chat-v3-0324"`。
* **`temperature`**: 控制模型输出的随机性。值越高，输出越随机。
* **`base_url`**: LLM API 的基础 URL。
* **`max_retries`**: API 请求的最大重试次数。
* **`max_tokens`**: 模型生成响应的最大 token 数。
* **`frequency_penalty`**: 对重复 token 的惩罚，值越高，模型越倾向于生成新的 token。
* **`api_key_path`**: 存储 API Key 的 JSON 文件路径。`get_api_key` 方法会从该文件中读取对应 `model_name` 的 API Key。

## `LLMManager`：LLM 管理器

`LLMManager` 是一个单例模式的类，负责存储和提供不同配置的 LLM 实例。

`LLMManager` 定义在 [`src/main_agent/llm_manager.py`](src/main_agent/llm_manager.py) 中，其结构如下：

```python
class LLMManager:
    """
    LLM 管理器，用于管理 LLM 配置组和实例化 LLM 模型。
    """
    def __init__(self):
        self._llm_configs: Dict[str, LLMConfig] = {}

    def set_llm_configs(self, llm_configs: Dict[str, LLMConfig]):
        """
        设置 LLM 配置组。
        """
        self._llm_configs = llm_configs

    def get_llm(self, config_name: str = "default", **override_params: Any) -> ChatOpenAI:
        """
        根据配置组名称和覆盖参数获取 LLM 实例。
        """
        if config_name not in self._llm_configs:
            raise ValueError(f"LLM config group '{config_name}' not found.")

        config = self._llm_configs[config_name].model_copy(update=override_params)
        api_key = config.get_api_key()

        llm = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            base_url=config.base_url,
            api_key=api_key,
            max_retries=config.max_retries,
            max_tokens=config.max_tokens,
            frequency_penalty=config.frequency_penalty,
        )
        return llm

# 全局 LLM 管理器实例
llm_manager = LLMManager()

def initialize_llm_manager(llm_configs: Dict[str, LLMConfig]):
    """
    初始化全局 LLM 管理器实例的配置。
    """
    llm_manager.set_llm_configs(llm_configs)
```

### 主要方法

* **`set_llm_configs(self, llm_configs: Dict[str, LLMConfig])`**:
  * 用于设置一个 LLM 配置组，其中键是配置名称（例如 `"default"`、`"summarization"`），值是对应的 `LLMConfig` 实例。
  * 这个方法通常在 Agent 启动时调用，如 `src/main_agent/graph.py` 中所示。

* **`get_llm(self, config_name: str = "default", **override_params: Any) -> ChatOpenAI`**:
  * 根据指定的 `config_name` 获取一个 `ChatOpenAI` LLM 实例。
  * 允许通过 `override_params` 动态覆盖配置中的任何参数，例如在特定调用中临时调整 `temperature` 或 `max_tokens`。
  * 如果找不到指定的配置名称，则会抛出 `ValueError`。

### 全局实例和初始化

`llm_manager = LLMManager()` 创建了一个全局的 `LLMManager` 实例。
`initialize_llm_manager(llm_configs: Dict[str, LLMConfig])` 函数用于在 Agent 启动时初始化这个全局实例的配置。

这种 LLM 管理机制使得 XieShui Agent 能够：

* **灵活配置**: 轻松定义和切换不同用途的 LLM 配置。
* **集中管理**: 所有 LLM 相关的配置和实例化逻辑都集中在一个地方。
* **动态调整**: 在运行时根据需要覆盖 LLM 参数，以适应不同的任务场景。
