"""
规划服务 HTTP 客户端工具

通过 HTTP 调用独立的 RAG 规划服务（8003端口），
避免后端镜像包含 ChromaDB 等重型依赖。
"""
import logging
import os
from typing import Optional

import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# RAG 服务地址（从环境变量读取，默认使用 Docker 网络内的服务名）
PLANNING_SERVICE_URL = os.getenv(
    "PLANNING_SERVICE_URL",
    "http://localhost:8003"
)


@tool
def planning_consult(query: str, mode: str = "auto") -> str:
    """
    乡村规划咨询 - 基于知识库的智能问答

    **何时使用：**
    - 用户询问乡村发展规划、政策解读、产业建议
    - 涉及乡村旅游、农业政策、技术指导等问题

    **参数：**
    - query: 用户问题
    - mode: 工作模式
      - "fast": 快速模式（最多2次工具调用）
      - "deep": 深度模式（最多5次工具调用）
      - "auto": 自动模式（AI自主选择）

    **返回：**
    - 基于知识库的专业建议
    """
    try:
        url = f"{PLANNING_SERVICE_URL}/api/chat/planning"

        with httpx.Timeout(30.0):
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json={
                        "message": query,
                        "mode": mode,
                        "thread_id": None  # 简单场景不需要会话保持
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                # 解析 SSE 流式响应
                full_content = ""
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        import json
                        try:
                            data = json.loads(line[6:])  # 去掉 "data: " 前缀
                            if data.get("type") == "content":
                                full_content += data.get("content", "")
                            elif data.get("type") == "end":
                                break
                        except json.JSONDecodeError:
                            continue

                return full_content or "抱歉，未能获取到回答。"

    except httpx.HTTPError as e:
        logger.error(f"规划服务调用失败: {e}")
        return f"⚠️ 规划服务暂时不可用，请稍后再试。错误: {str(e)}"
    except Exception as e:
        logger.error(f"规划咨询工具异常: {e}")
        return f"❌ 咨询过程中出现错误: {str(e)}"


# 导出为 LangChain 工具
__all__ = ["planning_consult"]
