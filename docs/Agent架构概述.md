# Agent 架构概述

本文档旨在概述 XieShui Agent 的核心架构。XieShui Agent 是一个基于 LangGraph 构建的智能代理，它通过定义清晰的状态、节点和边来管理复杂的对话流程和任务执行。

## 核心组件

XieShui Agent 的核心组件包括：

1. **LangGraph 图 (`graph.py`)**: 定义了 Agent 的整体运行流程，包括各个处理步骤（节点）以及它们之间的转换逻辑（边）。
2. **Agent 状态管理 (`state.py`)**: 定义了 `MainAgentState`，用于在 Agent 运行过程中维护和传递关键信息，如对话历史、用户信息和当前 Agent 模式。
3. **LLM 管理 (`llm_manager.py`)**: 负责配置和实例化不同用途的语言模型（LLM），确保 Agent 能够根据需要调用合适的模型。
4. **Agent 配置 (`conf.py`)**: 提供了 Agent 的全局配置选项。

## 架构概览

XieShui Agent 的架构设计旨在实现模块化和可扩展性。通过将不同的功能封装在独立的节点中，并利用 LangGraph 的状态管理和条件路由能力，Agent 能够灵活地响应用户输入并执行复杂的任务。

### LangGraph 的应用

LangGraph 是构建 XieShui Agent 的核心框架。它允许我们以图形化的方式定义 Agent 的行为，每个节点代表一个特定的处理步骤（例如，欢迎消息、工具执行、总结），而边则定义了这些步骤之间的流转逻辑。这种设计使得 Agent 的逻辑清晰可见，易于理解和维护。

### 状态管理

`MainAgentState` 是 Agent 运行时的单一事实来源。它包含了 Agent 在整个交互过程中所需的所有数据。通过在节点之间传递和更新这个状态对象，Agent 能够保持上下文，并根据历史信息做出决策。

### LLM 管理

`LLMManager` 提供了一个统一的接口来管理和获取不同配置的 LLM 实例。这使得 Agent 能够根据任务需求（例如，摘要、工具调用、通用对话）选择最合适的 LLM，从而优化性能和成本。

### 配置管理

`Configuration` 类用于定义 Agent 的全局配置。这使得 Agent 的行为可以通过外部配置进行调整，而无需修改核心代码。

## 后续文档

在后续文档中，我们将深入探讨每个核心组件的细节：

* [Agent 状态管理](Agent状态管理.md)
* [LLM 管理](LLM管理.md)
* [Agent 图结构](Agent图结构.md)
