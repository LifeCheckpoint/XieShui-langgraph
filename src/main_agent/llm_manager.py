from __future__ import annotations

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
    max_tokens: int = Field(default=16384, description="LLM 最大 token 数")
    frequency_penalty: float = Field(default=0.0, description="LLM 频率惩罚")
    api_key_path: str = Field(default=(Path(__file__).parent / "api_key.json").as_posix(), description="API Key 文件路径")

    def get_api_key(self) -> Optional[str]:
        json_text = Path(self.api_key_path).read_text(encoding="utf-8").strip()
        return json.loads(json_text).get(self.model_name)

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