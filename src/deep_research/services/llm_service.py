"""
Deep Research LLM 服务
统一的LLM调用管理器，消除重复的错误处理代码
"""

import json
from typing import Type, Optional, Any, Dict, List
from pathlib import Path

import jinja2
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from aiopath import AsyncPath

from src.deep_research.core.retry import research_retry
from src.deep_research.core.errors import LLMInvokeError, PromptTemplateError
from src.deep_research.core.paths import get_prompt_path, get_log_path
from src.main_agent.llm_manager import llm_manager

import datetime
from pathlib import Path

# 创建调试日志
log_file = Path("src/deep_research/logs/debug_llm_service.log")
log_file.parent.mkdir(exist_ok=True)

def write_log(message: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

class LLMService:
    """统一的LLM调用服务"""
    
    def __init__(self):
        self._template_cache: Dict[str, str] = {}
    
    @research_retry(max_attempts=3, fallback_strategy="manual_parse")
    async def structured_invoke(
        self,
        prompt: str,
        model_class: Type[BaseModel],
        config_name: str = "default"
    ) -> BaseModel:
        """
        结构化LLM调用
        
        Args:
            prompt: 提示内容
            model_class: 期望的返回模型类
            config_name: LLM配置名称
            
        Returns:
            BaseModel: 结构化响应
        """
        try:
            llm = llm_manager.get_llm(config_name=config_name).with_structured_output(model_class)
            response: BaseModel = await llm.ainvoke([HumanMessage(content=prompt)]) # type: ignore
            
            # 确保返回正确的模型实例
            write_log(f"-------- LLM Service 调用成功 --------")
            write_log(f"期望的模型类: {model_class}")
            write_log(f"LLM响应内容: {response}")
            write_log(f"响应类型: {type(response)}")
            return response
        except Exception as e:
            raise LLMInvokeError(f"Structured invoke failed: {e}", 1, e)
    
    @research_retry(max_attempts=3, fallback_strategy="default_value")
    async def simple_invoke(
        self,
        prompt: str,
        config_name: str = "default"
    ) -> str:
        """
        简单LLM调用
        
        Args:
            prompt: 提示内容
            config_name: LLM配置名称
            
        Returns:
            str: 响应内容
        """
        try:
            llm = llm_manager.get_llm(config_name=config_name)
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            # 安全地提取内容
            content = response.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                return "\n".join(str(item) for item in content)
            else:
                return str(content)
        except Exception as e:
            raise LLMInvokeError(f"Simple invoke failed: {e}", 1, e)
    
    async def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        渲染提示模板
        
        Args:
            template_name: 模板文件名
            context: 模板上下文
            
        Returns:
            str: 渲染后的提示
        """
        try:
            # 尝试从缓存获取模板
            if template_name not in self._template_cache:
                template_path = get_prompt_path(template_name)
                template_content = await AsyncPath(template_path).read_text(encoding="utf-8")
                self._template_cache[template_name] = template_content
            
            template = jinja2.Template(self._template_cache[template_name])
            return template.render(context)
            
        except Exception as e:
            raise PromptTemplateError(f"Template rendering failed: {e}", template_name)
    
    async def invoke_with_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        model_class: Type[BaseModel],
        config_name: str = "default"
    ) -> BaseModel:
        """
        使用模板进行结构化调用
        
        Args:
            template_name: 模板文件名
            context: 模板上下文
            model_class: 期望的返回模型类
            config_name: LLM配置名称
            
        Returns:
            BaseModel: 结构化响应
        """
        prompt = await self.render_template(template_name, context)
        return await self.structured_invoke(prompt, model_class, config_name)
    
    async def invoke_with_template_simple(
        self,
        template_name: str,
        context: Dict[str, Any],
        config_name: str = "default"
    ) -> str:
        """
        使用模板进行简单调用
        
        Args:
            template_name: 模板文件名
            context: 模板上下文
            config_name: LLM配置名称
            
        Returns:
            str: 响应内容
        """
        prompt = await self.render_template(template_name, context)
        return await self.simple_invoke(prompt, config_name)
    
    async def manual_parse_response(
        self,
        prompt: str,
        model_class: Type[BaseModel],
        config_name: str = "default"
    ) -> BaseModel:
        """
        手动解析响应（当结构化输出失败时的降级方案）
        
        Args:
            prompt: 提示内容
            model_class: 期望的返回模型类
            config_name: LLM配置名称
            
        Returns:
            BaseModel: 解析后的模型实例
        """
        try:
            # 构建降级提示
            schema_example = self._get_schema_example(model_class)
            fallback_prompt = f"{prompt}\n\n请严格按照以下JSON格式回复，不要包含任何其他文字:\n{schema_example}"
            
            # 使用非结构化LLM调用
            response_content = await self.simple_invoke(fallback_prompt, config_name)
            
            # 清理响应内容
            content = str(response_content).strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # 解析JSON并创建模型实例
            parsed_content = json.loads(content)
            return model_class(**parsed_content)
            
        except Exception as e:
            raise LLMInvokeError(f"Manual parsing failed: {e}", 1, e)
    
    def _get_schema_example(self, model_class: Type[BaseModel]) -> str:
        """获取模型的JSON示例"""
        try:
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
    
    def clear_template_cache(self) -> None:
        """清空模板缓存"""
        self._template_cache.clear()
    
    async def warmup_templates(self, template_names: List[str]) -> None:
        """预热模板缓存"""
        for template_name in template_names:
            try:
                template_path = get_prompt_path(template_name)
                template_content = await AsyncPath(template_path).read_text(encoding="utf-8")
                self._template_cache[template_name] = template_content
            except Exception:
                # 忽略不存在的模板
                pass


# 全局LLM服务实例
llm_service = LLMService()


# 便捷函数
async def invoke_research_plan(topic: str, research_cycles: List[Dict], total_cycles: int) -> Any:
    """生成研究计划的便捷函数"""
    from pydantic import BaseModel, Field
    
    class ResearchPlan(BaseModel):
        research_status: str = Field(..., description="研究现状")
        research_goal: str = Field(..., description="研究目标")
        research_range: str = Field(..., description="研究范围")
        research_method: str = Field(..., description="研究方法")
    
    # 自适应裁剪findings以避免token溢出
    adapted_cycles = _adapt_cycles_for_token_limit(research_cycles)
    
    context = {
        "topic": topic,
        "research_cycles": adapted_cycles,
        "research_total_cycles": total_cycles,
        "current_cycle_index": len(research_cycles) + 1
    }
    
    return await llm_service.invoke_with_template(
        "research_plan.txt",
        context,
        ResearchPlan
    )


async def invoke_search_queries(topic: str, research_plan: Dict) -> Any:
    """生成搜索查询的便捷函数"""
    from pydantic import BaseModel, Field
    
    class SearchQuery(BaseModel):
        content: str = Field(..., description="要搜索的内容")
        reason: str = Field(..., description="进行此搜索的原因")
        max_result: int = Field(..., description="期望的最大结果数")
    
    class SearchQueries(BaseModel):
        queries: List[SearchQuery]
    
    context = {
        "topic": topic,
        "research_plan": research_plan
    }
    
    return await llm_service.invoke_with_template(
        "search_instruction.txt",
        context,
        SearchQueries
    )


def _adapt_cycles_for_token_limit(research_cycles: List[Dict], max_token_length: int = 128000) -> List[Dict]:
    """自适应裁剪研究循环数据以避免token溢出"""
    adapted_cycles = []
    
    for cycle in research_cycles:
        adapted_cycle = cycle.copy()
        findings = cycle.get("findings", [])
        
        if findings:
            # 计算findings总长度
            total_length = sum(len(str(finding)) for finding in findings)
            
            if total_length > max_token_length:
                # 计算每个finding的最大长度
                max_finding_length = max_token_length // len(findings)
                
                adapted_findings = []
                for finding in findings:
                    finding_str = str(finding)
                    if len(finding_str) > max_finding_length:
                        adapted_findings.append(finding_str[:max_finding_length] + "...")
                    else:
                        adapted_findings.append(finding)
                
                adapted_cycle["findings"] = adapted_findings
        
        adapted_cycles.append(adapted_cycle)
    
    return adapted_cycles