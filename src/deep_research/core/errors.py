"""
Deep Research 错误处理模块
定义研究过程中的各种异常类型
"""

from typing import Optional, Any


class ResearchError(Exception):
    """研究过程中的基础异常类"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LLMInvokeError(ResearchError):
    """LLM调用相关异常"""
    
    def __init__(self, message: str, attempt: int, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.attempt = attempt
        self.original_error = original_error


class ValidationError(ResearchError):
    """数据验证异常"""
    
    def __init__(self, message: str, field_name: Optional[str] = None, field_value: Optional[Any] = None):
        super().__init__(message)
        self.field_name = field_name
        self.field_value = field_value


class StateTransitionError(ResearchError):
    """状态转换异常"""
    
    def __init__(self, message: str, current_state: str, expected_state: str):
        super().__init__(message)
        self.current_state = current_state
        self.expected_state = expected_state


class PromptTemplateError(ResearchError):
    """提示模板加载异常"""
    
    def __init__(self, message: str, template_path: str):
        super().__init__(message)
        self.template_path = template_path


class CitationError(ResearchError):
    """引用管理异常"""
    
    def __init__(self, message: str, citation_id: Optional[str] = None):
        super().__init__(message)
        self.citation_id = citation_id