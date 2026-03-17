"""
模型选择中间件

根据运行时 context 中的 model_id 动态选择 LLM 模型。
基于 LangChain 官方文档的 Middleware + Runtime Context 模式。
"""
import logging
from typing import Callable, Awaitable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

from ...config import AVAILABLE_MODELS, DEFAULT_MODEL_ID
from ...utils import ModelManager

logger = logging.getLogger(__name__)

# 预初始化所有模型实例（避免每次请求都创建）
MODEL_INSTANCES: dict = {}


def _initialize_models():
    """初始化所有模型实例"""
    global MODEL_INSTANCES
    if MODEL_INSTANCES:
        return  # 已初始化

    for model_id, config in AVAILABLE_MODELS.items():
        try:
            manager = ModelManager(provider=config["provider"])
            MODEL_INSTANCES[model_id] = manager.get_chat_model(model=config["model_name"])
            logger.info(f"模型实例初始化成功: {model_id} ({config['model_name']})")
        except Exception as e:
            logger.error(f"模型实例初始化失败: {model_id} - {e}")


class ModelSelectionMiddleware(AgentMiddleware):
    """
    模型选择中间件

    根据运行时 context 中的 model_id 动态选择 LLM 模型。
    支持异步调用（astream_events / ainvoke）。
    """

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """同步版本 - 用于同步调用"""
        return self._select_model_and_call(request, handler)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """异步版本 - 用于异步调用 (astream_events / ainvoke)"""
        return await self._aselect_model_and_call(request, handler)

    def _select_model_and_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """选择模型并调用（同步）"""
        _initialize_models()

        model_id = self._get_model_id(request)
        model = self._get_model_instance(model_id)

        logger.info(f"模型选择: {model_id}")
        return handler(request.override(model=model))

    async def _aselect_model_and_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """选择模型并调用（异步）"""
        _initialize_models()

        model_id = self._get_model_id(request)
        model = self._get_model_instance(model_id)

        logger.info(f"模型选择: {model_id}")
        return await handler(request.override(model=model))

    def _get_model_id(self, request: ModelRequest) -> str:
        """从 context 获取模型 ID"""
        model_id = DEFAULT_MODEL_ID
        if request.runtime and request.runtime.context:
            model_id = getattr(request.runtime.context, "model_id", DEFAULT_MODEL_ID)
        return model_id

    def _get_model_instance(self, model_id: str):
        """获取模型实例"""
        model = MODEL_INSTANCES.get(model_id)
        if model is None:
            logger.warning(f"未找到模型 {model_id}，使用默认模型 {DEFAULT_MODEL_ID}")
            model = MODEL_INSTANCES.get(DEFAULT_MODEL_ID)
        if model is None:
            raise RuntimeError(f"无法获取模型实例: {model_id}")
        return model


# 创建中间件实例
model_selection_middleware = ModelSelectionMiddleware()