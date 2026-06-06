"""
抖音彩蛋内容采集器
使用 Playwright 模拟浏览器访问抖音搜索页，提取视频数据。

⚠️ 合规提醒：
- 仅采集公开可见内容，不突破登录墙
- 单IP每分钟≤5次请求
- 所有采集内容标注来源平台和原作者
- 提供"删除我的内容"入口
"""
import asyncio
import json
import os
from datetime import datetime

from playwright.async_api import async_playwright, Page

from config import SEARCH_KEYWORDS, REQUEST_INTERVAL, MAX_PAGES_PER_KEYWORD, OUTPUT_DIR
from models import ScrapedEgg, SourcePlatform, EggCategory


CATEGORY_KEYWORDS = {
    EggCategory.BOOK: ["书", "教科书", "课本", "小说", "读物", "图书"],
    EggCategory.MAGAZINE: ["杂志", "国家地理", "期刊", "画报"],
    EggCategory.LETTER: ["信", "手写", "明信片", "纸条", "留言"],
    EggCategory.BLIND_BOX: ["盲盒", "惊喜", "礼物", "宝箱"],
}


def classify_content(text: str) -> EggCategory:
    """根据文本内容自动分类"""
    text_lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    if scores:
        return max(scores, key=scores.get)
    return EggCategory.OTHER


async def scroll_page(page: Page, times: int = 3, delay: float = 2.0):
    """模拟人类滚动页面"""
    for _ in range(times):
        await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
        await asyncio.sleep(delay)


async def extract_video_cards(page: Page) -> list[dict]:
    """从抖音搜索结果页提取视频卡片数据"""
    cards = []
    selectors = [
        "div[class*='search-result-card']",
        "li[class*='video-card']",
        "div[data-e2e='scroll-list'] > div",
        "div.search-result-item",
    ]

    elements = []
    for selector in selectors:
        elements = await page.query_selector_all(selector)
        if elements:
            break

    for el in elements[:20]:
        try:
            card_data = await el.evaluate("""
                (el) => {
                    const titleEl = el.querySelector('[class*="title"], h3, p[class*="desc"]');
                    const authorEl = el.querySelector('[class*="author"], [class*="nickname"]');
                    const imgEl = el.querySelector('img');
                    const linkEl = el.closest('a') || el.querySelector('a');
                    return {
                        title: titleEl ? titleEl.textContent.trim() : '',
                        author: authorEl ? authorEl.textContent.trim() : '',
                        cover: imgEl ? imgEl.src : '',
                        link: linkEl ? linkEl.href : ''
                    };
                }
            """)
            if card_data.get("title"):
                cards.append(card_data)
        except Exception:
            continue

    return cards


async def scrape_douyin(keyword: str, max_pages: int = MAX_PAGES_PER_KEYWORD) -> list[ScrapedEgg]:
    """采集指定关键词的抖音视频"""
    results = []
    search_url = f"https://www.douyin.com/search/{keyword}?type=general"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"[DY] 搜索关键词: {keyword}")
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            for page_num in range(max_pages):
                print(f"  第 {page_num + 1}/{max_pages} 页")
                await scroll_page(page, times=3, delay=REQUEST_INTERVAL)
                cards = await extract_video_cards(page)
                print(f"  提取到 {len(cards)} 条视频")

                for card in cards:
                    egg = ScrapedEgg(
                        title=card.get("title", ""),
                        description=card.get("title", ""),
                        category=classify_content(card.get("title", "")),
                        images=[card["cover"]] if card.get("cover") else [],
                        source_url=card.get("link", search_url),
                        source_platform=SourcePlatform.DOUYIN,
                        source_author=card.get("author"),
                        placed_at=datetime.now(),
                    )
                    results.append(egg)

                if page_num < max_pages - 1:
                    await asyncio.sleep(REQUEST_INTERVAL)

        except Exception as e:
            print(f"[DY] 采集异常: {e}")
        finally:
            await browser.close()

    return results


async def run_douyin_scraper():
    """运行抖音采集主流程"""
    all_results = []
    keywords = SEARCH_KEYWORDS.get("douyin", [])

    for keyword in keywords:
        eggs = await scrape_douyin(keyword)
        all_results.extend(eggs)
        await asyncio.sleep(REQUEST_INTERVAL * 2)

    # 去重
    seen_urls = set()
    unique_results = []
    for egg in all_results:
        if egg.source_url not in seen_urls:
            seen_urls.add(egg.source_url)
            unique_results.append(egg)

    # 保存结果
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"douyin_eggs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in unique_results], f, ensure_ascii=False, indent=2)

    print(f"\n✅ 抖音采集完成: {len(unique_results)} 条数据 → {output_path}")
    return unique_results


if __name__ == "__main__":
    asyncio.run(run_douyin_scraper())
