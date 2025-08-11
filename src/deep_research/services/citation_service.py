"""
Deep Research 引用管理服务
统一管理学术引用和文献映射
"""

from typing import Dict, List, Any, Optional, Tuple
import re

from src.deep_research.core.errors import CitationError


class CitationService:
    """引用管理服务"""
    
    def __init__(self):
        self._citation_counter = 1
        self._citation_cache: Dict[str, Dict[str, Any]] = {}
    
    def create_citation_map(self, raw_content_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], Dict[str, Dict[str, Any]]]:
        """
        从原始内容列表创建引用映射
        
        Args:
            raw_content_list: 原始内容列表，每个元素包含summary, raw_text, url等字段
            
        Returns:
            Tuple: (用于LLM的引用列表, 完整的引用映射)
        """
        cite_llm_list = []
        cite_mapping = {}
        
        for content in raw_content_list:
            if not isinstance(content, dict):
                continue
            
            # 生成引用ID
            cite_id = f"C{self._citation_counter}"
            self._citation_counter += 1
            
            # 提取必要信息
            cite_summary = content.get("summary", "No summary available.")
            cite_text = content.get("raw_text", "No raw content available.")
            cite_url = content.get("url", "No URL available.")
            
            # 用于LLM的简化引用信息
            cite_llm_list.append({
                "cite_id": cite_id,
                "summary": cite_summary
            })
            
            # 完整的引用映射
            cite_mapping[cite_id] = {
                "summary": cite_summary,
                "text": cite_text,
                "url": cite_url,
                "created_at": self._get_current_timestamp()
            }
            
            # 缓存引用信息
            self._citation_cache[cite_id] = cite_mapping[cite_id].copy()
        
        return cite_llm_list, cite_mapping
    
    def get_citations_for_section(self, cite_ids: List[str], citations: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        获取特定章节的引用信息
        
        Args:
            cite_ids: 引用ID列表
            citations: 完整的引用映射
            
        Returns:
            List: 格式化的引用信息列表
        """
        section_citations = []
        
        for cite_id in cite_ids:
            if cite_id not in citations:
                raise CitationError(f"Citation not found: {cite_id}", cite_id)
            
            citation = citations[cite_id]
            section_citations.append({
                "cite_id": cite_id,
                "summary": citation["summary"],
                "text": citation["text"]
            })
        
        return section_citations
    
    def generate_bibliography(self, citations: Dict[str, Dict[str, Any]]) -> str:
        """
        生成参考文献列表
        
        Args:
            citations: 引用映射
            
        Returns:
            str: 格式化的参考文献
        """
        bibliography = "\n## 参考文献\n\n"
        
        # 按照引用ID排序
        sorted_citations = sorted(citations.items(), key=lambda x: self._extract_citation_number(x[0]))
        
        for cite_id, citation in sorted_citations:
            url = citation.get("url", "No URL available")
            summary = citation.get("summary", "No summary available")
            
            # 简化URL显示
            display_url = self._simplify_url(url)
            
            bibliography += f"- **{cite_id}**: {display_url}\n"
            if len(summary) > 100:
                bibliography += f"  *{summary[:100]}...*\n"
            else:
                bibliography += f"  *{summary}*\n"
            bibliography += "\n"
        
        return bibliography
    
    def validate_citation_references(self, text: str, available_citations: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        验证文本中的引用引用是否有效
        
        Args:
            text: 包含引用的文本
            available_citations: 可用的引用映射
            
        Returns:
            Tuple: (是否所有引用都有效, 无效引用列表)
        """
        # 使用正则表达式查找所有引用
        citation_pattern = r'\[C\d+\]'
        found_citations = re.findall(citation_pattern, text)
        
        invalid_citations = []
        for citation in found_citations:
            cite_id = citation[1:-1]  # 移除方括号
            if cite_id not in available_citations:
                invalid_citations.append(cite_id)
        
        return len(invalid_citations) == 0, invalid_citations
    
    def format_citation_reference(self, cite_ids: List[str]) -> str:
        """
        格式化引用引用
        
        Args:
            cite_ids: 引用ID列表
            
        Returns:
            str: 格式化的引用引用
        """
        if not cite_ids:
            return ""
        
        # 验证引用ID格式
        valid_cite_ids = []
        for cite_id in cite_ids:
            if re.match(r'^C\d+$', cite_id):
                valid_cite_ids.append(cite_id)
            else:
                raise CitationError(f"Invalid citation ID format: {cite_id}", cite_id)
        
        # 排序并格式化
        sorted_ids = sorted(valid_cite_ids, key=self._extract_citation_number)
        return "".join(f"[{cite_id}]" for cite_id in sorted_ids)
    
    def extract_citations_from_text(self, text: str) -> List[str]:
        """
        从文本中提取所有引用ID
        
        Args:
            text: 包含引用的文本
            
        Returns:
            List: 引用ID列表
        """
        citation_pattern = r'\[C(\d+)\]'
        matches = re.findall(citation_pattern, text)
        return [f"C{num}" for num in matches]
    
    def get_citation_statistics(self, citations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取引用统计信息
        
        Args:
            citations: 引用映射
            
        Returns:
            Dict: 统计信息
        """
        total_citations = len(citations)
        
        # 统计URL类型
        url_types = {"arxiv": 0, "github": 0, "academic": 0, "other": 0}
        
        for citation in citations.values():
            url = citation.get("url", "").lower()
            if "arxiv" in url:
                url_types["arxiv"] += 1
            elif "github" in url:
                url_types["github"] += 1
            elif any(domain in url for domain in ["edu", "nature", "science", "ieee", "acm"]):
                url_types["academic"] += 1
            else:
                url_types["other"] += 1
        
        return {
            "total_citations": total_citations,
            "url_types": url_types,
            "citation_ids": list(citations.keys())
        }
    
    def merge_citation_maps(
        self,
        map1: Dict[str, Dict[str, Any]],
        map2: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        合并两个引用映射
        
        Args:
            map1: 第一个引用映射
            map2: 第二个引用映射
            
        Returns:
            Dict: 合并后的引用映射
        """
        merged = map1.copy()
        
        for cite_id, citation in map2.items():
            if cite_id in merged:
                # 如果ID冲突，重新分配ID
                new_cite_id = self._generate_unique_citation_id(merged)
                merged[new_cite_id] = citation
            else:
                merged[cite_id] = citation
        
        return merged
    
    def cleanup_unused_citations(
        self,
        citations: Dict[str, Dict[str, Any]],
        used_citation_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        清理未使用的引用
        
        Args:
            citations: 原始引用映射
            used_citation_ids: 已使用的引用ID列表
            
        Returns:
            Dict: 清理后的引用映射
        """
        return {
            cite_id: citation
            for cite_id, citation in citations.items()
            if cite_id in used_citation_ids
        }
    
    def _extract_citation_number(self, cite_id: str) -> int:
        """从引用ID中提取数字"""
        try:
            return int(cite_id[1:])  # 移除'C'前缀
        except (ValueError, IndexError):
            return 0
    
    def _simplify_url(self, url: str) -> str:
        """简化URL显示"""
        if len(url) <= 80:
            return url
        
        # 尝试保留域名和路径的重要部分
        if "arxiv.org" in url:
            match = re.search(r'arxiv\.org/(?:abs/|pdf/)?(\d+\.\d+)', url)
            if match:
                return f"arxiv.org/abs/{match.group(1)}"
        
        # 对于其他URL，截断并添加省略号
        return url[:77] + "..."
    
    def _generate_unique_citation_id(self, existing_citations: Dict[str, Any]) -> str:
        """生成唯一的引用ID"""
        while True:
            cite_id = f"C{self._citation_counter}"
            if cite_id not in existing_citations:
                self._citation_counter += 1
                return cite_id
            self._citation_counter += 1
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        try:
            import datetime
            return datetime.datetime.now().isoformat()
        except Exception:
            return "unknown"
    
    def reset_counter(self) -> None:
        """重置引用计数器"""
        self._citation_counter = 1
        self._citation_cache.clear()
    
    def get_cached_citations(self) -> Dict[str, Dict[str, Any]]:
        """获取缓存的引用信息"""
        return self._citation_cache.copy()


# 全局引用服务实例
citation_service = CitationService()