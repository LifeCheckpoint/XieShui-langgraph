from src.graph_manager.knowledge_core.knowledge_graph_integration import KnowledgeGraphIntegration

kgi = None

def init_kgi():
    """
    初始化 KnowledgeGraphIntegration 实例。
    这个函数可以在需要时调用，确保 kgi 在使用前已被正确初始化。
    """
    global kgi
    # 初始化一个 KnowledgeGraphIntegration 实例，供所有工具函数使用
    kgi = KnowledgeGraphIntegration()
    # 加载默认知识图谱集
    kgi.reload_graphs()
