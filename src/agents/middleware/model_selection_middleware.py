"""
模型选择中间件

根据运行时 context 中的 model_id 动态选择 LLM 模型。
基于 LangChain 官方文档的 Middleware + Runtime Context 模式。
"""
import logging
from typing import Callable

from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

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


@wrap_model_call
def model_selection_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """
    根据运行时 context 动态选择模型

    从 request.runtime.context 获取用户选择的 model_id，
    然后覆盖请求中的模型实例。

    Args:
        request: 模型请求对象
        handler: 下一个处理器

    Returns:
        模型响应
    """
    # 确保模型已初始化
    _initialize_models()

    # 从 context 获取用户选择的 model_id
    model_id = DEFAULT_MODEL_ID
    if request.runtime and request.runtime.context:
        model_id = getattr(request.runtime.context, "model_id", DEFAULT_MODEL_ID)

    # 获取对应的模型实例
    model = MODEL_INSTANCES.get(model_id)
    if model is None:
        logger.warning(f"未找到模型 {model_id}，使用默认模型 {DEFAULT_MODEL_ID}")
        model = MODEL_INSTANCES.get(DEFAULT_MODEL_ID)

    if model is None:
        raise RuntimeError(f"无法获取模型实例: {model_id}")

    logger.debug(f"模型选择: {model_id}")

    # 覆盖请求中的模型
    return handler(request.override(model=model))