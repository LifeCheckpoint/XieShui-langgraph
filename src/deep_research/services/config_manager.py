"""
Deep Research 配置管理器
提供统一的配置管理和参数调整功能
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from src.deep_research.core.errors import ValidationError
from src.deep_research.core.paths import get_module_root


class LLMConfigName(str, Enum):
    """LLM配置名称枚举"""
    DEFAULT = "default"
    LONG_WRITING = "long_writing"
    DEFAULT_MORE_TOKEN = "default_moretoken"


@dataclass
class ResearchConfig:
    """研究配置"""
    # 研究参数
    max_research_cycles: int = 5
    max_findings_per_cycle: int = 20
    max_token_length: int = 128000
    
    # 搜索参数
    default_search_results: int = 5
    max_search_results: int = 15
    search_timeout: int = 30
    
    # 阅读参数
    max_reading_list: int = 5
    max_skimming_list: int = 10
    content_max_length: int = 80000
    
    # 写作参数
    section_max_words: int = 800
    section_min_words: int = 500
    report_min_words: int = 8000
    report_max_words: int = 15000
    
    # LLM配置
    default_llm_config: str = LLMConfigName.DEFAULT.value
    default_long_llm_config: str = LLMConfigName.DEFAULT_MORE_TOKEN.value
    long_writing_llm_config: str = LLMConfigName.LONG_WRITING.value
    
    # 重试配置
    max_retry_attempts: int = 3
    enable_fallback_parsing: bool = True
    enable_logging: bool = True
    
    # 缓存配置
    enable_template_cache: bool = True
    enable_citation_cache: bool = True
    max_cache_size: int = 1000


@dataclass
class PathConfig:
    """路径配置"""
    prompt_templates_dir: str = "utils/nodes"
    logs_dir: str = "logs"
    output_dir: str = "data/deep_research"
    backup_dir: str = "backup"


@dataclass
class ValidationConfig:
    """验证配置"""
    enable_state_validation: bool = True
    enable_data_validation: bool = True
    strict_type_checking: bool = False
    validate_citations: bool = True


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "deep_research_config.json"
        self._research_config = ResearchConfig()
        self._path_config = PathConfig()
        self._validation_config = ValidationConfig()
        self._custom_configs: Dict[str, Any] = {}
        
        # 尝试加载配置文件
        self.load_config()
    
    @property
    def research(self) -> ResearchConfig:
        """获取研究配置"""
        return self._research_config
    
    @property
    def paths(self) -> PathConfig:
        """获取路径配置"""
        return self._path_config
    
    @property
    def validation(self) -> ValidationConfig:
        """获取验证配置"""
        return self._validation_config
    
    def get_custom_config(self, key: str, default: Any = None) -> Any:
        """获取自定义配置"""
        return self._custom_configs.get(key, default)
    
    def set_custom_config(self, key: str, value: Any) -> None:
        """设置自定义配置"""
        self._custom_configs[key] = value
    
    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            config_path = get_module_root() / self.config_file
        else:
            config_path = Path(config_path)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新各个配置
                if "research" in config_data:
                    self._update_research_config(config_data["research"])
                
                if "paths" in config_data:
                    self._update_path_config(config_data["paths"])
                
                if "validation" in config_data:
                    self._update_validation_config(config_data["validation"])
                
                if "custom" in config_data:
                    self._custom_configs.update(config_data["custom"])
                    
            except Exception as e:
                raise ValidationError(f"Failed to load config file: {e}")
    
    def save_config(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            config_path = get_module_root() / self.config_file
        else:
            config_path = Path(config_path)
        
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            "research": asdict(self._research_config),
            "paths": asdict(self._path_config),
            "validation": asdict(self._validation_config),
            "custom": self._custom_configs
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValidationError(f"Failed to save config file: {e}")
    
    def reset_to_defaults(self) -> None:
        """重置所有配置为默认值"""
        self._research_config = ResearchConfig()
        self._path_config = PathConfig()
        self._validation_config = ValidationConfig()
        self._custom_configs.clear()
    
    def validate_config(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            bool: 配置是否有效
            
        Raises:
            ValidationError: 配置无效时抛出
        """
        # 验证研究配置
        if self._research_config.max_research_cycles <= 0:
            raise ValidationError("max_research_cycles must be positive")
        
        if self._research_config.max_token_length <= 0:
            raise ValidationError("max_token_length must be positive")
        
        if self._research_config.max_retry_attempts <= 0:
            raise ValidationError("max_retry_attempts must be positive")
        
        # 验证LLM配置名称
        valid_llm_configs = [config.value for config in LLMConfigName]
        if self._research_config.default_llm_config not in valid_llm_configs:
            raise ValidationError(f"Invalid default_llm_config: {self._research_config.default_llm_config}")
        
        if self._research_config.long_writing_llm_config not in valid_llm_configs:
            raise ValidationError(f"Invalid long_writing_llm_config: {self._research_config.long_writing_llm_config}")
        
        # 验证搜索参数
        if self._research_config.default_search_results > self._research_config.max_search_results:
            raise ValidationError("default_search_results cannot be greater than max_search_results")
        
        # 验证阅读参数
        if self._research_config.max_reading_list <= 0:
            raise ValidationError("max_reading_list must be positive")
        
        # 验证写作参数
        if self._research_config.section_min_words > self._research_config.section_max_words:
            raise ValidationError("section_min_words cannot be greater than section_max_words")
        
        if self._research_config.report_min_words > self._research_config.report_max_words:
            raise ValidationError("report_min_words cannot be greater than report_max_words")
        
        return True
    
    def get_llm_config_for_task(self, task: str) -> str:
        """
        根据任务类型获取适当的LLM配置
        
        Args:
            task: 任务类型 ("planning", "searching", "reading", "writing", "finetune")
            
        Returns:
            str: LLM配置名称
        """
        task_configs = {
            "planning": self._research_config.default_llm_config,
            "searching": self._research_config.default_llm_config,
            "reading": self._research_config.long_writing_llm_config,
            "writing": self._research_config.long_writing_llm_config,
            "finetune": self._research_config.default_long_llm_config
        }
        
        return task_configs.get(task, self._research_config.default_llm_config)
    
    def get_search_config(self) -> Dict[str, int]:
        """获取搜索相关配置"""
        return {
            "default_results": self._research_config.default_search_results,
            "max_results": self._research_config.max_search_results,
            "timeout": self._research_config.search_timeout
        }
    
    def get_writing_config(self) -> Dict[str, int]:
        """获取写作相关配置"""
        return {
            "section_min_words": self._research_config.section_min_words,
            "section_max_words": self._research_config.section_max_words,
            "report_min_words": self._research_config.report_min_words,
            "report_max_words": self._research_config.report_max_words
        }
    
    def update_research_cycles(self, cycles: int) -> None:
        """更新研究循环次数"""
        if cycles <= 0:
            raise ValidationError("Research cycles must be positive")
        self._research_config.max_research_cycles = cycles
    
    def enable_debug_mode(self) -> None:
        """启用调试模式"""
        self._research_config.enable_logging = True
        self._validation_config.enable_state_validation = True
        self._validation_config.enable_data_validation = True
        self._validation_config.strict_type_checking = True
    
    def enable_production_mode(self) -> None:
        """启用生产模式"""
        self._research_config.enable_logging = False
        self._validation_config.strict_type_checking = False
    
    def _update_research_config(self, config_data: Dict[str, Any]) -> None:
        """更新研究配置"""
        for key, value in config_data.items():
            if hasattr(self._research_config, key):
                setattr(self._research_config, key, value)
    
    def _update_path_config(self, config_data: Dict[str, Any]) -> None:
        """更新路径配置"""
        for key, value in config_data.items():
            if hasattr(self._path_config, key):
                setattr(self._path_config, key, value)
    
    def _update_validation_config(self, config_data: Dict[str, Any]) -> None:
        """更新验证配置"""
        for key, value in config_data.items():
            if hasattr(self._validation_config, key):
                setattr(self._validation_config, key, value)
    
    def export_config_template(self, output_path: Union[str, Path]) -> None:
        """导出配置模板"""
        template = {
            "research": asdict(ResearchConfig()),
            "paths": asdict(PathConfig()),
            "validation": asdict(ValidationConfig()),
            "custom": {
                "example_setting": "example_value",
                "user_preferences": {}
            }
        }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "research_cycles": self._research_config.max_research_cycles,
            "llm_configs": {
                "default": self._research_config.default_llm_config,
                "long_writing": self._research_config.long_writing_llm_config
            },
            "search": {
                "default_results": self._research_config.default_search_results,
                "max_results": self._research_config.max_search_results
            },
            "validation": {
                "state_validation": self._validation_config.enable_state_validation,
                "data_validation": self._validation_config.enable_data_validation
            },
            "custom_configs_count": len(self._custom_configs)
        }


# 全局配置管理器实例
config_manager = ConfigManager()