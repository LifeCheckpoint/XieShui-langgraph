"""
Deep Research 路径工具模块
提供统一的路径管理和文件操作功能
"""

from pathlib import Path
from typing import Union, Optional
import datetime

from src.deep_research.core.errors import PromptTemplateError


def get_prompt_path(template_name: str) -> Path:
    """
    获取提示模板文件的路径
    
    Args:
        template_name: 模板名称 (如 "research_plan.txt")
        
    Returns:
        Path: 模板文件路径
        
    Raises:
        PromptTemplateError: 模板文件不存在时抛出
    """
    template_path = Path(__file__).parent.parent / "utils" / "nodes" / template_name
    
    if not template_path.exists():
        raise PromptTemplateError(
            f"Prompt template not found: {template_name}",
            str(template_path)
        )
    
    return template_path


def get_log_path(log_name: str, create_dir: bool = True) -> Path:
    """
    获取日志文件路径
    
    Args:
        log_name: 日志文件名 (如 "planning_success.log")
        create_dir: 是否自动创建目录
        
    Returns:
        Path: 日志文件路径
    """
    log_path = Path(__file__).parent.parent / "logs" / log_name
    
    if create_dir:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    return log_path


def ensure_output_dir() -> Path:
    """
    确保输出目录存在
    
    Returns:
        Path: 输出目录路径
    """
    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "deep_research"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_output_path(filename: Optional[str] = None) -> Path:
    """
    获取输出文件路径
    
    Args:
        filename: 文件名，如果为None则生成默认文件名
        
    Returns:
        Path: 输出文件路径
    """
    output_dir = ensure_output_dir()
    
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_report_{timestamp}.md"
    
    return output_dir / filename


def make_valid_filename(filename: str) -> str:
    """
    将字符串转换为有效的文件名
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 有效的文件名
    """
    invalid_chars = ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.']
    valid_filename = ''
    
    for char in filename:
        if char not in invalid_chars:
            valid_filename += char
        else:
            valid_filename += '_'
    
    return valid_filename.strip()


def get_relative_path(full_path: Union[str, Path], base_path: Union[str, Path]) -> Path:
    """
    获取相对路径
    
    Args:
        full_path: 完整路径
        base_path: 基础路径
        
    Returns:
        Path: 相对路径
    """
    full_path = Path(full_path)
    base_path = Path(base_path)
    
    try:
        return full_path.relative_to(base_path)
    except ValueError:
        # 如果无法计算相对路径，返回绝对路径
        return full_path


def ensure_file_exists(file_path: Union[str, Path], create_empty: bool = False) -> bool:
    """
    确保文件存在
    
    Args:
        file_path: 文件路径
        create_empty: 如果文件不存在，是否创建空文件
        
    Returns:
        bool: 文件是否存在
    """
    file_path = Path(file_path)
    
    if file_path.exists():
        return True
    
    if create_empty:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        return True
    
    return False


def get_module_root() -> Path:
    """
    获取deep_research模块根目录
    
    Returns:
        Path: 模块根目录路径
    """
    return Path(__file__).parent.parent


def get_workspace_root() -> Path:
    """
    获取工作空间根目录
    
    Returns:
        Path: 工作空间根目录路径
    """
    return Path(__file__).parent.parent.parent.parent


def backup_file(file_path: Union[str, Path], backup_suffix: str = ".bak") -> Path:
    """
    备份文件
    
    Args:
        file_path: 要备份的文件路径
        backup_suffix: 备份文件后缀
        
    Returns:
        Path: 备份文件路径
    """
    file_path = Path(file_path)
    backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
    
    if file_path.exists():
        import shutil
        shutil.copy2(file_path, backup_path)
    
    return backup_path