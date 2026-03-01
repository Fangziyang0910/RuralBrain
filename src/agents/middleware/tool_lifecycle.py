"""
工具生命周期管理模块

实现工具自适应 TTL（Time To Live）机制：
- 工具注册时赋予初始生命周期
- 每次使用工具时 TTL 续期
- 每轮对话所有已注册工具 TTL -1
- TTL 过期的工具自动卸载
- 支持关键工具设置"钉住"（永不卸载）
"""
import logging
from typing import Optional

from pydantic import BaseModel, Field

from ...config import DEFAULT_TOOL_TTL, DEFAULT_TOOL_EXTENSION

logger = logging.getLogger(__name__)


class TTLConfig(BaseModel):
    """
    TTL 配置模型

    定义工具的生命周期策略，支持配置驱动的方式设置每个技能/工具的 TTL 行为。

    默认值从全局配置读取，支持在 YAML 中覆盖。

    Attributes:
        base_ttl: 基础生命周期（轮数），工具注册时的初始 TTL
        extension: 使用后续期增量（轮数），工具被调用时的续期量
        pinned: 是否钉住，钉住的工具永不卸载
    """
    base_ttl: int = Field(default_factory=lambda: DEFAULT_TOOL_TTL, description="基础 TTL（轮数）")
    extension: int = Field(default_factory=lambda: DEFAULT_TOOL_EXTENSION, description="使用后续期（轮数）")
    pinned: bool = Field(default=False, description="是否钉住（永不卸载）")


class ToolLifecycle(BaseModel):
    """
    工具生命周期追踪模型

    追踪单个工具在会话中的生命周期状态，包括当前 TTL、注册时间、使用时间等。

    Attributes:
        tool_name: 工具名称
        skill_name: 所属技能名称
        current_ttl: 当前 TTL 值
        base_ttl: 基础 TTL 值（注册时设置）
        extension: 使用后续期增量
        pinned: 是否钉住（永不卸载）
        registration_round: 注册时的轮次
        last_used_round: 最后使用的轮次
    """
    tool_name: str = Field(..., description="工具名称")
    skill_name: str = Field(..., description="所属技能名称")
    current_ttl: int = Field(..., description="当前 TTL 值", ge=0)
    base_ttl: int = Field(..., description="基础 TTL 值", ge=1)
    extension: int = Field(default=3, description="使用后续期增量", ge=0)
    pinned: bool = Field(default=False, description="是否钉住")
    registration_round: int = Field(..., description="注册时的轮次", ge=0)
    last_used_round: Optional[int] = Field(None, description="最后使用的轮次")

    def is_expired(self) -> bool:
        """
        检查工具是否过期

        Returns:
            如果工具已过期返回 True，否则返回 False
            钉住的工具永远不会过期
        """
        return not self.pinned and self.current_ttl <= 0

    def renew(self) -> int:
        """
        续期工具 TTL

        将当前 TTL 设置为 base_ttl + extension
        钉住的工具 TTL 保持不变

        Returns:
            续期后的 TTL 值
        """
        if not self.pinned:
            self.current_ttl = self.base_ttl + self.extension
            logger.debug(
                f"工具续期: {self.tool_name} "
                f"(TTL: {self.current_ttl}, base: {self.base_ttl}, extension: {self.extension})"
            )
        return self.current_ttl

    def decrement(self) -> int:
        """
        TTL 减 1

        每轮对话开始时调用，钉住的工具 TTL 不减少

        Returns:
            减少后的 TTL 值
        """
        if not self.pinned and self.current_ttl > 0:
            self.current_ttl -= 1
        return self.current_ttl

    def mark_used(self, round: int) -> None:
        """
        标记工具已被使用

        Args:
            round: 当前轮次
        """
        self.last_used_round = round

    def get_status(self) -> dict:
        """
        获取工具生命周期状态（用于调试和监控）

        Returns:
            包含生命周期信息的字典
        """
        return {
            "tool_name": self.tool_name,
            "skill_name": self.skill_name,
            "current_ttl": self.current_ttl,
            "base_ttl": self.base_ttl,
            "extension": self.extension,
            "pinned": self.pinned,
            "registration_round": self.registration_round,
            "last_used_round": self.last_used_round,
            "expired": self.is_expired(),
        }


__all__ = [
    "TTLConfig",
    "ToolLifecycle",
]
