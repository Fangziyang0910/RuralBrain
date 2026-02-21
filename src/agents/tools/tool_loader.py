"""
工具加载器 - 支持按名称动态加载工具实例

用于动态工具注册系统，允许在运行时根据工具名称加载工具实例。
"""
import logging
from typing import Callable, Dict, List, Optional

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class ToolLoader:
    """
    工具加载器

    职责：
    1. 维护工具名称到工具实例的映射
    2. 根据工具名称列表动态加载工具实例
    3. 延迟加载，避免循环导入

    设计说明：
    - 使用 lambda 函数延迟导入，避免模块级循环依赖
    - 工具按功能分组（检测、内置、RAG）
    """

    def __init__(self):
        """初始化工具加载器"""
        self._tool_factories: Dict[str, Callable[[], BaseTool]] = {}
        self._register_all_tools()
        logger.info(f"ToolLoader 初始化完成，已注册 {len(self._tool_factories)} 个工具")

    def _register_all_tools(self):
        """注册所有可用工具"""
        # ==================== 检测工具 ====================
        self._tool_factories.update({
            "pest_detection_tool": self._load_pest_detection_tool,
            "rice_detection_tool": self._load_rice_detection_tool,
            "cow_detection_tool": self._load_cow_detection_tool,
        })

        # ==================== 内置工具 ====================
        self._tool_factories.update({
            "pricing_tool": self._load_pricing_tool,
            "marketing_tool": self._load_marketing_tool,
            "farm_inspection_tool": self._load_farm_inspection_tool,
            "disease_prediction_tool": self._load_disease_prediction_tool,
        })

        # ==================== 规划工具 ====================
        self._tool_factories.update({
            "planning_consult": self._load_planning_consult,
        })

        # ==================== RAG 工具 ====================
        self._tool_factories.update({
            "document_list_tool": self._load_document_list_tool,
            "document_overview_tool": self._load_document_overview_tool,
            "key_points_search_tool": self._load_key_points_search_tool,
            "knowledge_search_tool": self._load_knowledge_search_tool,
        })

    # ==================== 检测工具加载器 ====================

    def _load_pest_detection_tool(self) -> BaseTool:
        from .pest_detection_tool import pest_detection_tool
        return pest_detection_tool

    def _load_rice_detection_tool(self) -> BaseTool:
        from .rice_detection_tool import rice_detection_tool
        return rice_detection_tool

    def _load_cow_detection_tool(self) -> BaseTool:
        from .cow_detection_tool import cow_detection_tool
        return cow_detection_tool

    # ==================== 内置工具加载器 ====================

    def _load_pricing_tool(self) -> BaseTool:
        from .pricing_tool import pricing_tool
        return pricing_tool

    def _load_marketing_tool(self) -> BaseTool:
        from .marketing_tool import marketing_tool
        return marketing_tool

    def _load_farm_inspection_tool(self) -> BaseTool:
        from .farm_inspection_tool import farm_inspection_tool
        return farm_inspection_tool

    def _load_disease_prediction_tool(self) -> BaseTool:
        from .disease_prediction_tool import disease_prediction_tool
        return disease_prediction_tool

    # ==================== 规划工具加载器 ====================

    def _load_planning_consult(self) -> BaseTool:
        from .planning_service_tool import planning_consult
        return planning_consult

    # ==================== RAG 工具加载器 ====================

    def _load_document_list_tool(self) -> BaseTool:
        from src.rag.core.tools import document_list_tool
        return document_list_tool

    def _load_document_overview_tool(self) -> BaseTool:
        from src.rag.core.tools import document_overview_tool
        return document_overview_tool

    def _load_key_points_search_tool(self) -> BaseTool:
        from src.rag.core.tools import key_points_search_tool
        return key_points_search_tool

    def _load_knowledge_search_tool(self) -> BaseTool:
        from src.rag.core.tools import knowledge_search_tool
        return knowledge_search_tool

    # ==================== 公共接口 ====================

    def load_tools_by_names(self, tool_names: List[str]) -> List[BaseTool]:
        """
        根据工具名称列表加载工具实例

        Args:
            tool_names: 工具名称列表

        Returns:
            工具实例列表

        注意：
            - 未知工具名称会被跳过，记录警告日志
            - 返回的工具顺序与 tool_names 一致
        """
        tools = []
        for name in tool_names:
            if name in self._tool_factories:
                try:
                    tool = self._tool_factories[name]()
                    tools.append(tool)
                    logger.debug(f"加载工具: {name}")
                except Exception as e:
                    logger.error(f"加载工具 {name} 失败: {e}")
            else:
                logger.warning(f"未知工具名称: {name}，跳过")

        if tools:
            logger.info(f"成功加载 {len(tools)}/{len(tool_names)} 个工具")
        return tools

    def get_available_tool_names(self) -> List[str]:
        """
        获取所有可用的工具名称

        Returns:
            工具名称列表
        """
        return list(self._tool_factories.keys())

    def is_tool_available(self, tool_name: str) -> bool:
        """
        检查工具是否可用

        Args:
            tool_name: 工具名称

        Returns:
            如果工具可用返回 True，否则返回 False
        """
        return tool_name in self._tool_factories

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取单个工具实例

        Args:
            tool_name: 工具名称

        Returns:
            工具实例，如果工具不存在返回 None
        """
        if tool_name in self._tool_factories:
            try:
                return self._tool_factories[tool_name]()
            except Exception as e:
                logger.error(f"加载工具 {tool_name} 失败: {e}")
                return None
        return None


# ==================== 全局单例 ====================

_global_tool_loader: Optional[ToolLoader] = None


def get_tool_loader() -> ToolLoader:
    """
    获取全局工具加载器实例

    Returns:
        ToolLoader 实例
    """
    global _global_tool_loader
    if _global_tool_loader is None:
        _global_tool_loader = ToolLoader()
    return _global_tool_loader


def reset_tool_loader():
    """
    重置全局工具加载器实例

    主要用于测试
    """
    global _global_tool_loader
    _global_tool_loader = None


__all__ = [
    "ToolLoader",
    "get_tool_loader",
    "reset_tool_loader",
]
