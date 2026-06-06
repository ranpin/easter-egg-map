"""
彩蛋地图数据采集 - 主入口
统一调度小红书、抖音采集任务，合并输出结构化数据。

用法:
    python main.py                  # 运行全部采集器
    python main.py --platform xhs   # 仅运行小红书
    python main.py --platform dy    # 仅运行抖音
"""
import argparse
import asyncio
import json
import os
from datetime import datetime

from config import OUTPUT_DIR


async def run_all(platform: str = "all"):
    """运行采集任务"""
    all_eggs = []

    if platform in ("all", "xhs"):
        from xhs_scraper import run_xhs_scraper
        print("=" * 50)
        print("🔍 开始小红书采集...")
        print("=" * 50)
        xhs_eggs = await run_xhs_scraper()
        all_eggs.extend(xhs_eggs)

    if platform in ("all", "dy"):
        from douyin_scraper import run_douyin_scraper
        print("\n" + "=" * 50)
        print("🔍 开始抖音采集...")
        print("=" * 50)
        dy_eggs = await run_douyin_scraper()
        all_eggs.extend(dy_eggs)

    # 合并去重并保存
    seen_urls = set()
    unique_eggs = []
    for egg in all_eggs:
        data = egg.to_dict() if hasattr(egg, "to_dict") else egg
        url = data.get("source_url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_eggs.append(data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"all_eggs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_eggs, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 50}")
    print(f"✅ 采集完成! 共 {len(unique_eggs)} 条数据")
    print(f"📁 输出文件: {output_path}")
    print(f"{'=' * 50}")

    return unique_eggs


def main():
    parser = argparse.ArgumentParser(description="彩蛋地图数据采集工具")
    parser.add_argument(
        "--platform",
        choices=["all", "xhs", "dy"],
        default="all",
        help="指定采集平台: all(全部), xhs(小红书), dy(抖音)"
    )
    args = parser.parse_args()
    asyncio.run(run_all(args.platform))


if __name__ == "__main__":
    main()
