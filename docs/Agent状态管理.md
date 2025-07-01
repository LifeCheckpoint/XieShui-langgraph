# Agent 状态管理

在 XieShui Agent 中，`MainAgentState` 类负责管理 Agent 在整个交互过程中的状态。它是一个基于 Pydantic `BaseModel` 定义的数据结构，确保了状态的类型安全和易于序列化。

## `MainAgentState` 定义

`MainAgentState` 定义在 [`src/main_agent/utils/state.py`](src/main_agent/utils/state.py) 中，其结构如下：

```python
from __future__ import annotations

from typing import Annotated, List
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class MainAgentState(BaseModel):
    """
    Agent 状态模型
    """
    messages: Annotated[List[AnyMessage], add_messages] = Field(default=[], description="Agent 消息列表，包含交互历史，储存和传递对话内容")
    current_user_info: dict = Field(default={}, description="当前用户信息，包含用户的基本信息和偏好设置")
    agent_mode: str = Field(default="default", description="Agent 模式，指示当前的工作模式或任务类型", examples=["default", "research", "execution"])
```

## 字段说明

### `messages`

* **类型**: `Annotated[List[AnyMessage], add_messages]`
* **默认值**: `[]`
* **描述**: 这是一个消息列表，用于存储 Agent 与用户之间的所有交互历史。`AnyMessage` 可以是 LangChain 提供的任何消息类型（例如 `HumanMessage`、`AIMessage`、`ToolMessage` 等）。`Annotated` 和 `add_messages` 的使用表明这个字段在 LangGraph 中具有特殊行为，每次更新时会追加新的消息而不是完全覆盖。这对于维护完整的对话上下文至关重要。

### `current_user_info`

* **类型**: `dict`
* **默认值**: `{}`
* **描述**: 用于存储当前用户的相关信息，例如用户的偏好设置、个人资料或其他与用户会话相关的上下文数据。这使得 Agent 能够根据用户的具体情况进行个性化响应。

### `agent_mode`

* **类型**: `str`
* **默认值**: `"default"`
* **描述**: 指示 Agent 当前所处的工作模式或任务类型。例如，Agent 可能有“default”（默认）、“research”（研究）或“execution”（执行）等模式。不同的模式可以触发 Agent 内部不同的行为逻辑或工具集，从而实现多功能性。

## 状态管理的重要性

`MainAgentState` 在 XieShui Agent 的运行中扮演着核心角色：

* **上下文维护**: 通过 `messages` 字段，Agent 能够记住之前的对话内容，从而进行连贯且有意义的交流。
* **个性化响应**: `current_user_info` 允许 Agent 根据用户的特定信息调整其行为和响应。
* **行为路由**: `agent_mode` 字段可以作为 LangGraph 中条件边的判断依据，引导 Agent 进入不同的处理流程。

通过对 `MainAgentState` 的有效管理，XieShui Agent 能够实现复杂、有状态的交互逻辑。
