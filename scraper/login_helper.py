"""
Cookie登录助手 - 手动扫码/账密登录后自动保存Cookie
用法:
    python login_helper.py --platform xhs
    python login_helper.py --platform dy
"""
import argparse
import asyncio
import json
import os
from pathlib import Path

COOKIES_DIR = Path(__file__).parent / "cookies"


async def login_xhs():
    """小红书登录"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ 请先安装 playwright: pip install playwright && playwright install chromium")
        return

    os.makedirs(COOKIES_DIR, exist_ok=True)
    cookie_path = COOKIES_DIR / "xhs_cookies.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto("https://www.xiaohongshu.com/explore")

        print("\n" + "=" * 50)
        print("📱 请在浏览器中完成小红书登录（扫码或账密）")
        print("⏳ 登录成功后会自动检测并保存Cookie...")
        print("=" * 50 + "\n")

        # 等待登录成功（检测用户头像出现）
        try:
            await page.wait_for_selector('.user-avatar, .sidebar-user, [class*="avatar"]', timeout=300000)
            print("✅ 检测到登录成功！正在保存Cookie...")
        except Exception:
            print("⚠️ 等待超时，尝试直接保存当前Cookie...")

        cookies = await context.cookies()
        with open(cookie_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"💾 Cookie已保存到: {cookie_path}")
        print(f"📊 共保存 {len(cookies)} 个Cookie条目")
        await browser.close()


async def login_douyin():
    """抖音登录"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ 请先安装 playwright: pip install playwright && playwright install chromium")
        return

    os.makedirs(COOKIES_DIR, exist_ok=True)
    cookie_path = COOKIES_DIR / "dy_cookies.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto("https://www.douyin.com/search/%E6%97%85%E8%A1%8C")

        print("\n" + "=" * 50)
        print("📱 请在浏览器中完成抖音登录（扫码或手机号）")
        print("⏳ 登录成功后会自动检测并保存Cookie...")
        print("=" * 50 + "\n")

        try:
            await page.wait_for_selector('[class*="avatar"], [class*="user-info"]', timeout=300000)
            print("✅ 检测到登录成功！正在保存Cookie...")
        except Exception:
            print("⚠️ 等待超时，尝试直接保存当前Cookie...")

        cookies = await context.cookies()
        with open(cookie_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"💾 Cookie已保存到: {cookie_path}")
        print(f"📊 共保存 {len(cookies)} 个Cookie条目")
        await browser.close()


def main():
    parser = argparse.ArgumentParser(description="彩蛋地图Cookie登录助手")
    parser.add_argument("--platform", choices=["xhs", "dy"], required=True, help="平台: xhs(小红书) / dy(抖音)")
    args = parser.parse_args()

    if args.platform == "xhs":
        asyncio.run(login_xhs())
    else:
        asyncio.run(login_douyin())


if __name__ == "__main__":
    main()
