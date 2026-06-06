"""
彩蛋地图数据采集 - 主入口（v2）
基于 MediaCrawler 引擎，支持小红书/抖音自动采集 + 后处理

用法:
    python main.py                              # 全平台采集+后处理
    python main.py --platform xhs               # 仅小红书
    python main.py --platform dy                # 仅抖音
    python main.py --process-only               # 仅运行后处理（不采集）
    python main.py --keywords "旅行彩蛋,课本接头"  # 自定义关键词
"""
import argparse
import asyncio
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import yaml
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")
logger.add("logs/crawler_{time:YYYYMMDD}.log", rotation="10 MB", retention="30 days")


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
    return {}


async def crawl_xhs(keywords: list, max_notes: int, config: dict):
    """
    小红书采集 - 基于 MediaCrawler
    
    MediaCrawler 提供了完整的小红书API封装，包括：
    - 关键词搜索笔记
    - 笔记详情获取
    - 评论采集
    - Cookie自动管理
    
    参考: https://github.com/NanmiCoder/MediaCrawler
    """
    try:
        from media_platform.xhs.core import XiaoHongShuCrawler
        logger.info("✅ MediaCrawler 已安装，使用原生引擎采集小红书")
        
        # 使用MediaCrawler原生采集
        crawler = XiaoHongShuCrawler()
        # ... MediaCrawler 内部处理
        
    except ImportError:
        logger.warning("⚠️ MediaCrawler 未安装，使用内置轻量采集器")
        await _crawl_xhs_lightweight(keywords, max_notes, config)


async def _crawl_xhs_lightweight(keywords: list, max_notes: int, config: dict):
    """
    轻量级小红书采集器（MediaCrawler不可用时的降级方案）
    使用 Playwright + Cookie 模拟搜索
    """
    from playwright.async_api import async_playwright
    
    cookie_path = Path(__file__).parent / "cookies" / "xhs_cookies.json"
    if not cookie_path.exists():
        logger.error("❌ 未找到小红书Cookie，请先运行: python login_helper.py --platform xhs")
        return []
    
    with open(cookie_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    
    delay_cfg = config.get("crawl", {})
    min_delay = delay_cfg.get("request_delay_min", 3)
    max_delay = delay_cfg.get("request_delay_max", 8)
    
    all_notes = []
    output_dir = Path(config.get("output", {}).get("dir", "./output"))
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        for keyword in keywords:
            logger.info(f"🔍 搜索关键词: {keyword}")
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&type=1"
            
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(random.uniform(min_delay, max_delay))
                
                # 提取搜索结果中的笔记卡片
                cards = await page.query_selector_all('section.note-item, [class*="note-item"]')
                logger.info(f"  📋 找到 {len(cards)} 条结果")
                
                for i, card in enumerate(cards[:max_notes]):
                    try:
                        title_el = await card.query_selector('[class*="title"], .note-title')
                        title = await title_el.inner_text() if title_el else ""
                        
                        link_el = await card.query_selector('a[href*="/explore/"], a[href*="/search_result/"]')
                        href = await link_el.get_attribute("href") if link_el else ""
                        
                        img_el = await card.query_selector('img')
                        img_src = await img_el.get_attribute("src") if img_el else ""
                        
                        note = {
                            "note_id": href.split("/")[-1] if href else f"xhs_{keyword}_{i}",
                            "title": title,
                            "desc": "",
                            "image_list": [{"url": img_src}] if img_src else [],
                            "interact_info": {"liked_count": "0"},
                            "url": f"https://www.xiaohongshu.com{href}" if href and not href.startswith("http") else href,
                            "user": {"nickname": ""},
                        }
                        all_notes.append(note)
                    except Exception as e:
                        logger.debug(f"  ⚠️ 解析第{i+1}条失败: {e}")
                    
                    await asyncio.sleep(random.uniform(1, 2))
                
                await asyncio.sleep(random.uniform(min_delay, max_delay))
                
            except Exception as e:
                logger.error(f"  ❌ 搜索 '{keyword}' 失败: {e}")
        
        await browser.close()
    
    # 保存原始数据
    output_path = output_dir / f"xhs_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_notes, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 小红书原始数据已保存: {output_path} ({len(all_notes)} 条)")
    return all_notes


async def crawl_douyin(keywords: list, max_notes: int, config: dict):
    """抖音采集 - 基于 MediaCrawler 或降级方案"""
    try:
        from media_platform.douyin.core import DouYinCrawler
        logger.info("✅ MediaCrawler 已安装，使用原生引擎采集抖音")
    except ImportError:
        logger.warning("⚠️ MediaCrawler 未安装，使用内置轻量采集器")
        await _crawl_douyin_lightweight(keywords, max_notes, config)


async def _crawl_douyin_lightweight(keywords: list, max_notes: int, config: dict):
    """轻量级抖音采集器"""
    from playwright.async_api import async_playwright
    
    cookie_path = Path(__file__).parent / "cookies" / "dy_cookies.json"
    if not cookie_path.exists():
        logger.error("❌ 未找到抖音Cookie，请先运行: python login_helper.py --platform dy")
        return []
    
    with open(cookie_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    
    delay_cfg = config.get("crawl", {})
    min_delay = delay_cfg.get("request_delay_min", 3)
    max_delay = delay_cfg.get("request_delay_max", 8)
    
    all_notes = []
    output_dir = Path(config.get("output", {}).get("dir", "./output"))
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        for keyword in keywords:
            logger.info(f"🔍 搜索关键词: {keyword}")
            search_url = f"https://www.douyin.com/search/{keyword}?type=video"
            
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(random.uniform(min_delay, max_delay))
                
                # 提取视频卡片
                cards = await page.query_selector_all('[class*="search-result"], [data-e2e="scroll-list"] > div')
                logger.info(f"  📋 找到 {len(cards)} 条结果")
                
                for i, card in enumerate(cards[:max_notes]):
                    try:
                        title_el = await card.query_selector('[class*="title"], h3, p')
                        title = await title_el.inner_text() if title_el else ""
                        
                        link_el = await card.query_selector('a[href*="/video/"]')
                        href = await link_el.get_attribute("href") if link_el else ""
                        
                        img_el = await card.query_selector('img')
                        img_src = await img_el.get_attribute("src") if img_el else ""
                        
                        note = {
                            "aweme_id": href.split("/")[-1] if href else f"dy_{keyword}_{i}",
                            "desc": title,
                            "images": [{"url": img_src}] if img_src else [],
                            "digg_count": 0,
                            "share_url": href if href and href.startswith("http") else f"https://www.douyin.com{href}",
                            "author": {"nickname": ""},
                        }
                        all_notes.append(note)
                    except Exception as e:
                        logger.debug(f"  ⚠️ 解析第{i+1}条失败: {e}")
                    
                    await asyncio.sleep(random.uniform(1, 2))
                
                await asyncio.sleep(random.uniform(min_delay, max_delay))
                
            except Exception as e:
                logger.error(f"  ❌ 搜索 '{keyword}' 失败: {e}")
        
        await browser.close()
    
    output_path = output_dir / f"dy_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_notes, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 抖音原始数据已保存: {output_path} ({len(all_notes)} 条)")
    return all_notes


async def run(platform: str, keywords_override: list = None, max_notes: int = None, process_only: bool = False):
    """主运行流程"""
    config = load_config()
    
    if not process_only:
        keywords_cfg = config.get("search_keywords", {})
        max_notes = max_notes or config.get("crawl", {}).get("max_notes_per_keyword", 20)
        
        if platform in ("all", "xhs"):
            kw = keywords_override or keywords_cfg.get("xhs", ["旅行彩蛋"])
            logger.info(f"\n{'='*50}\n🔍 小红书采集 | 关键词: {kw}\n{'='*50}")
            await crawl_xhs(kw, max_notes, config)
        
        if platform in ("all", "dy"):
            kw = keywords_override or keywords_cfg.get("douyin", ["旅行彩蛋"])
            logger.info(f"\n{'='*50}\n🔍 抖音采集 | 关键词: {kw}\n{'='*50}")
            await crawl_douyin(kw, max_notes, config)
    
    # 后处理
    output_dir = config.get("output", {}).get("dir", "./output")
    logger.info(f"\n{'='*50}\n⚙️ 数据后处理...\n{'='*50}")
    
    from post_processor import process_all
    process_all(output_dir, output_dir, "./config.yaml")


def main():
    parser = argparse.ArgumentParser(description="彩蛋地图数据采集工具 v2")
    parser.add_argument("--platform", choices=["all", "xhs", "dy"], default="all")
    parser.add_argument("--keywords", type=str, help="逗号分隔的自定义关键词")
    parser.add_argument("--max-notes", type=int, help="每个关键词最大采集数")
    parser.add_argument("--process-only", action="store_true", help="仅运行后处理")
    args = parser.parse_args()
    
    keywords = args.keywords.split(",") if args.keywords else None
    asyncio.run(run(args.platform, keywords, args.max_notes, args.process_only))


if __name__ == "__main__":
    main()
