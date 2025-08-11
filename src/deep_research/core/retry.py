"""
Deep Research 重试机制模块
提供统一的重试装饰器和配置
"""

import asyncio
import json
from functools import wraps
from typing import Type, Optional, Callable, Any, Union
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from src.deep_research.core.errors import LLMInvokeError, ValidationError
from src.main_agent.llm_manager import llm_manager


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    fallback_strategy: str = "manual_parse"  # "manual_parse", "default_value", "raise"
    enable_logging: bool = True
    log_success: bool = True
    log_errors: bool = True


def research_retry(
    max_attempts: int = 3,
    fallback_strategy: str = "manual_parse",
    enable_logging: bool = True
):
    """
    研究专用重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        fallback_strategy: 失败策略 ("manual_parse", "default_value", "raise")
        enable_logging: 是否启用日志记录
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            config = RetryConfig(
                max_attempts=max_attempts,
                fallback_strategy=fallback_strategy,
                enable_logging=enable_logging
            )
            
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    
                    # 记录成功日志
                    if config.enable_logging and config.log_success:
                        await _log_success(func.__name__, attempt + 1, result)
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # 记录错误日志
                    if config.enable_logging and config.log_errors:
                        await _log_error(func.__name__, attempt + 1, e, *args, **kwargs)
                    
                    # 如果不是最后一次尝试，继续重试
                    if attempt < config.max_attempts - 1:
                        continue
                    
                    # 最后一次尝试失败，根据策略处理
                    if config.fallback_strategy == "raise":
                        raise e
                    elif config.fallback_strategy == "manual_parse":
                        return await _try_manual_parse(func.__name__, e, *args, **kwargs)
                    elif config.fallback_strategy == "default_value":
                        return await _get_default_value(func.__name__, e, *args, **kwargs)
            
            # 如果所有尝试都失败，抛出最后一个异常
            raise LLMInvokeError(
                f"Function {func.__name__} failed after {config.max_attempts} attempts",
                config.max_attempts,
                last_exception
            )
        
        return wrapper
    return decorator


async def _log_success(func_name: str, attempt: int, result: Any) -> None:
    """记录成功日志"""
    try:
        log_path = Path(__file__).parent.parent / "logs" / f"{func_name}_success.log"
        log_path.parent.mkdir(exist_ok=True)
        
        log_entry = f"Function {func_name} succeeded on attempt {attempt}\nResult: {str(result)[:500]}...\n\n"
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        # 静默忽略日志错误
        pass


async def _log_error(func_name: str, attempt: int, error: Exception, *args, **kwargs) -> None:
    """记录错误日志"""
    try:
        log_path = Path(__file__).parent.parent / "logs" / f"{func_name}_error.log"
        log_path.parent.mkdir(exist_ok=True)
        
        log_entry = f"Function {func_name} failed on attempt {attempt}\n"
        log_entry += f"Error: {error}\n"
        log_entry += f"Error type: {type(error).__name__}\n"
        log_entry += f"Args: {str(args)[:200]}...\n"
        log_entry += f"Kwargs: {str(kwargs)[:200]}...\n\n"
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        # 静默忽略日志错误
        pass


async def _try_manual_parse(func_name: str, error: Exception, *args, **kwargs) -> Any:
    """尝试手动解析JSON响应"""
    # 检查是否是JSON相关错误
    error_str = str(error).lower()
    if any(keyword in error_str for keyword in ["json", "validation", "expected value"]):
        try:
            # 尝试从kwargs中获取提示和模型类
            prompt = kwargs.get('prompt') or (args[0] if args else "")
            model_class = kwargs.get('model_class') or (args[1] if len(args) > 1 else None)
            
            if prompt and model_class:
                return await _fallback_llm_parse(prompt, model_class, func_name)
        except Exception:
            pass
    
    # 如果手动解析失败，返回默认值
    return await _get_default_value(func_name, error, *args, **kwargs)


async def _fallback_llm_parse(prompt: str, model_class: Type[BaseModel], func_name: str) -> BaseModel:
    """使用非结构化LLM进行降级解析"""
    try:
        fallback_llm = llm_manager.get_llm(config_name="default")
        
        # 构建降级提示
        schema_example = _get_schema_example(model_class)
        fallback_prompt = f"{prompt}\n\n请严格按照以下JSON格式回复，不要包含任何其他文字:\n{schema_example}"
        
        response = await fallback_llm.ainvoke([HumanMessage(content=fallback_prompt)])
        
        # 解析响应内容
        content = str(response.content).strip()
        
        # 移除可能的markdown代码块标记
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # 解析JSON
        parsed_content = json.loads(content)
        
        # 创建模型实例
        return model_class(**parsed_content)
        
    except Exception as e:
        raise ValidationError(f"Fallback parsing failed for {func_name}: {e}")


def _get_schema_example(model_class: Type[BaseModel]) -> str:
    """获取模型的JSON示例"""
    try:
        # 获取模型字段信息
        fields = model_class.model_fields
        example = {}
        
        for field_name, field_info in fields.items():
            if hasattr(field_info, 'description') and field_info.description:
                example[field_name] = field_info.description
            else:
                example[field_name] = f"示例{field_name}"
        
        return json.dumps(example, ensure_ascii=False, indent=2)
    except Exception:
        return '{"field": "value"}'


async def _get_default_value(func_name: str, error: Exception, *args, **kwargs) -> Any:
    """获取默认值"""
    # 根据函数名返回合适的默认值
    if "research_plan" in func_name.lower():
        from pydantic import BaseModel, Field
        
        class DefaultResearchPlan(BaseModel):
            research_status: str = Field(default="研究初始化失败，使用默认配置")
            research_goal: str = Field(default="进行基础研究分析")
            research_range: str = Field(default="基础主题相关内容")
            research_method: str = Field(default="标准文献检索和分析方法")
        
        return DefaultResearchPlan()
    
    elif "search_queries" in func_name.lower():
        from pydantic import BaseModel, Field
        
        class DefaultSearchQuery(BaseModel):
            content: str
            reason: str 
            max_result: int
            
        class DefaultSearchQueries(BaseModel):
            queries: list[DefaultSearchQuery]
        
        # 从args中获取主题
        topic = ""
        if args and hasattr(args[0], 'get'):
            topic = args[0].get('topic', '未知主题')
        
        return DefaultSearchQueries(queries=[
            DefaultSearchQuery(
                content=f"{topic} 基本概念",
                reason=f"了解{topic}的基础知识",
                max_result=5
            )
        ])
    
    # 返回空字典作为默认值
    return {}