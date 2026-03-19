"""
模型选择中间件

根据运行时 context 中的 model_id 动态选择 LLM 模型。
基于 LangChain 官方文档的 Middleware + Runtime Context 模式。
"""
import logging
import threading
from typing import Callable, Awaitable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

from ...config import AVAILABLE_MODELS, DEFAULT_MODEL_ID
from ...utils import ModelManager

logger = logging.getLogger(__name__)

# 预初始化所有模型实例（避免每次请求都创建）
MODEL_INSTANCES: dict = {}
_INITIALIZATION_LOCK = threading.Lock()
_INITIALIZATION_ATTEMPTED = False
_INITIALIZATION_ERRORS: dict = {}  # 缓存初始化失败原因


def _initialize_models():
    """初始化所有模型实例（线程安全）"""
    global MODEL_INSTANCES, _INITIALIZATION_ATTEMPTED, _INITIALIZATION_ERRORS

    # 快速检查：已初始化过则直接返回
    if MODEL_INSTANCES:
        return

    # 加锁确保线程安全
    with _INITIALIZATION_LOCK:
        # 双重检查：可能其他线程已经完成初始化
        if MODEL_INSTANCES or _INITIALIZATION_ATTEMPTED:
            return

        _INITIALIZATION_ATTEMPTED = True

        for model_id, config in AVAILABLE_MODELS.items():
            try:
                manager = ModelManager(provider=config["provider"])
                MODEL_INSTANCES[model_id] = manager.get_chat_model(model=config["model_name"])
                logger.info(f"模型实例初始化成功: {model_id} ({config['model_name']})")
            except Exception as e:
                _INITIALIZATION_ERRORS[model_id] = str(e)
                logger.error(f"模型实例初始化失败: {model_id} - {e}")

        # 如果所有模型都初始化失败，记录警告
        if not MODEL_INSTANCES:
            logger.warning("所有模型初始化失败，后续请求将快速失败")


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

        logger.debug(f"模型选择: {model_id}")
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
            # 检查是否有初始化失败的记录
            if model_id in _INITIALIZATION_ERRORS:
                raise RuntimeError(
                    f"模型 {model_id} 初始化失败: {_INITIALIZATION_ERRORS[model_id]}"
                )

            logger.warning(f"未找到模型 {model_id}，使用默认模型 {DEFAULT_MODEL_ID}")
            model = MODEL_INSTANCES.get(DEFAULT_MODEL_ID)

            if model is None and DEFAULT_MODEL_ID in _INITIALIZATION_ERRORS:
                raise RuntimeError(
                    f"默认模型 {DEFAULT_MODEL_ID} 初始化失败: {_INITIALIZATION_ERRORS[DEFAULT_MODEL_ID]}"
                )

        if model is None:
            raise RuntimeError(
                f"无法获取模型实例: {model_id}。"
                f"可用模型: {list(MODEL_INSTANCES.keys()) or '无'}"
            )
        return model


# 创建中间件实例
model_selection_middleware = ModelSelectionMiddleware()