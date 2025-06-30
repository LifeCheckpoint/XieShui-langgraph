"""
榭水主 Agent 配置文件
"""

from __future__ import annotations

from pydantic import BaseModel, Field

class Configuration(BaseModel):
    """
    MainAgent 配置文件模型
    """
    extra_system_prompt: str = Field(default="", description="额外系统提示词")

__all__ = ["Configuration"]