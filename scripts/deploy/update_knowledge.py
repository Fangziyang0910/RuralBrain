#!/usr/bin/env python3
"""
RuralBrain 知识库更新命令行工具

支持增量更新和全量重建知识库，无需重启服务。

用法:
    python update_knowledge.py --source ./data/new_doc.pdf
    python update_knowledge.py --source-dir ./data/policies --force
    python update_knowledge.py --source-dir ./src/data --category policies
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 默认配置
# 注意：RAG 已集成到主 Agent，API 地址已变更
DEFAULT_API_URL = "http://localhost:8081"
API_ENDPOINT = "/api/v1/knowledge/update"


class KnowledgeUpdater:
    """知识库更新器"""

    def __init__(self, api_url: str = DEFAULT_API_URL):
        self.api_url = api_url.rstrip("/")
        self.endpoint = f"{self.api_url}{API_ENDPOINT}"

    def update(
        self,
        source: Optional[str] = None,
        source_dir: Optional[str] = None,
        force_rebuild: bool = False,
        category: Optional[str] = None,
        timeout: int = 600,
    ) -> dict:
        """
        更新知识库

        Args:
            source: 单个文档路径
            source_dir: 文档目录路径
            force_rebuild: 是否全量重建
            category: 文档类别 (policies/cases)
            timeout: 超时时间（秒）

        Returns:
            API 响应结果
        """
        # 构建请求数据
        request_data = {
            "force_rebuild": force_rebuild,
        }

        if source:
            request_data["source"] = str(Path(source).absolute())
        elif source_dir:
            request_data["source_dir"] = str(Path(source_dir).absolute())
        else:
            raise ValueError("必须提供 --source 或 --source-dir 参数")

        if category:
            request_data["category"] = category

        # 发送请求
        logger.info(f"正在更新知识库...")
        logger.info(f"API 端点: {self.endpoint}")
        logger.info(f"请求参数: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

        try:
            start_time = time.time()

            response = requests.post(
                self.endpoint,
                json=request_data,
                timeout=timeout,
                headers={"Content-Type": "application/json"},
            )

            duration = time.time() - start_time

            # 检查响应
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ 知识库更新成功！")
                logger.info(f"   模式: {result.get('mode')}")
                logger.info(f"   新增文档: {result.get('documents_added')}")
                logger.info(f"   新增切片: {result.get('chunks_added')}")
                if result.get('documents_removed', 0) > 0:
                    logger.info(f"   删除文档: {result.get('documents_removed')}")
                logger.info(f"   耗时: {result.get('duration')}s")
                logger.info(f"   消息: {result.get('message')}")
                return result
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_detail)
                except:
                    pass
                logger.error(f"❌ 更新失败 (HTTP {response.status_code}): {error_detail}")
                sys.exit(1)

        except requests.exceptions.Timeout:
            logger.error(f"❌ 请求超时（超过 {timeout} 秒）")
            logger.error("   提示：大文档可能需要更长时间，可以使用 --timeout 参数增加超时时间")
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 无法连接到 API 服务: {self.endpoint}")
            logger.error("   请确保 Planning Service 正在运行")
            logger.error(f"   启动命令: docker-compose -f docker-compose.dev.yml up -d")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ 请求失败: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="RuralBrain 知识库更新工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 更新单个文档
  python update_knowledge.py --source ./data/new_policy.pdf

  # 批量更新目录中的文档
  python update_knowledge.py --source-dir ./data/policies

  # 全量重建知识库
  python update_knowledge.py --source-dir ./data --force

  # 指定文档类别
  python update_knowledge.py --source-dir ./data/policies --category policies

  # 使用自定义 API 地址
  python update_knowledge.py --source ./data/doc.pdf --api-url http://localhost:8081 # RAG 已集成到主 Agent
        """
    )

    parser.add_argument(
        "--source", "-s",
        help="单个文档路径",
    )
    parser.add_argument(
        "--source-dir", "-d",
        help="文档目录路径（批量处理）",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="全量重建模式（清空后重新构建）",
    )
    parser.add_argument(
        "--category", "-c",
        choices=["policies", "cases"],
        help="文档类别",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Planning Service API 地址（默认: {DEFAULT_API_URL}）",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=600,
        help="请求超时时间（秒，默认: 600）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅验证参数，不实际执行更新",
    )

    args = parser.parse_args()

    # 验证参数
    if not args.source and not args.source_dir:
        parser.error("必须提供 --source 或 --source-dir 参数")

    if args.source and args.source_dir:
        parser.error("--source 和 --source-dir 不能同时使用")

    # 验证文件/目录存在
    if args.source:
        source_path = Path(args.source)
        if not source_path.exists():
            logger.error(f"❌ 文件不存在: {args.source}")
            sys.exit(1)
    elif args.source_dir:
        source_dir = Path(args.source_dir)
        if not source_dir.exists():
            logger.error(f"❌ 目录不存在: {args.source_dir}")
            sys.exit(1)
        if not source_dir.is_dir():
            logger.error(f"❌ 路径不是目录: {args.source_dir}")
            sys.exit(1)

    # Dry run 模式
    if args.dry_run:
        logger.info("🔍 Dry run 模式（仅验证参数）")
        logger.info(f"   源: {args.source or args.source_dir}")
        logger.info(f"   模式: {'全量重建' if args.force else '增量更新'}")
        logger.info(f"   类别: {args.category or '未指定'}")
        logger.info(f"   API: {args.api_url}")
        logger.info("✓ 参数验证通过")
        sys.exit(0)

    # 执行更新
    updater = KnowledgeUpdater(api_url=args.api_url)
    updater.update(
        source=args.source,
        source_dir=args.source_dir,
        force_rebuild=args.force,
        category=args.category,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
