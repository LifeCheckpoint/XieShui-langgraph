"""
榭水主 Agent 配置文件
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Dict
from src.main_agent.utils.llm_manager import LLMConfig

class Configuration(BaseModel):
    """
    MainAgent 配置文件模型
    """
    extra_system_prompt: str = Field(default="", description="额外系统提示词")
    llm_configs: Dict[str, LLMConfig] = Field(
        default_factory=lambda: {
            "default": LLMConfig(),
            "summarization": LLMConfig(temperature=0.2),
            "agent_execution": LLMConfig(temperature=0.3),
        },
        description="LLM 配置组"
    )

__all__ = ["Configuration"]