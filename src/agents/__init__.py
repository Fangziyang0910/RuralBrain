"""农业智能代理模块

该模块包含各类农业相关的智能代理实现。

注意：Agent 实例应通过 service/server.py 的 get_agent() 函数延迟加载，
不要在模块级别导入 agent 实例，以避免在环境变量加载前触发模型初始化。

使用方式：
    from service.server import get_agent
    agent = get_agent()
"""

__all__ = []  # 不再导出 agent 实例，通过 get_agent() 获取