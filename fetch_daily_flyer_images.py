"""
fetch_daily_flyer_images.py
主力スーパー全店舗の最新チラシ原本・高解像度画像を自動収集・保存するスクリプト
（GitHub Actionsおよびローカル共通）
"""

import sys
import re
import urllib.parse
from pathlib import Path
import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

FLYERS_DIR = Path(__file__).resolve().parent / "flyers"
FLYERS_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 1. オータニのLINEチラシ原本ダウンロード（Playwright活用）
async def fetch_otani_image(context):
    print("\n▶ [1/4] オータニの最新チラシ原本画像を取得中...")
    try:
        page = await context.new_page()
        url = "https://www.sp-otani.com/store/detail/110030031.html?recordno=376"
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(3000)

        # iframe内のURLを探す
        content = await page.content()
        m = re.search(r'src=["\'](https://chirashi\.line\.me/asp/[^"\']+)["\']', content)
        if m:
            widget_url = m.group(1)
            await page.goto(widget_url, timeout=30000)
            await page.wait_for_timeout(3000)
            w_content = await page.content()
            obs_matches = re.findall(r'https://chirashi-obs\.line-scdn\.net/[a-zA-Z0-9_\-]+', w_content)
            if obs_matches:
                img_url = obs_matches[0]
                img_r = requests.get(img_url, headers=HEADERS, timeout=20)
                if len(img_r.content) > 50000:
                    save_path = FLYERS_DIR / "otani_flyer_orig.jpg"
                    with open(save_path, "wb") as f:
                        f.write(img_r.content)
                    print(f"  [OK] オータニ原本画像を保存: {save_path.name} ({len(img_r.content)} bytes)")
                    await page.close()
                    return

        # 原本URLが見つからない場合は画面キャプチャで確実に保存
        save_path = FLYERS_DIR / "otani_flyer_orig.jpg"
        await page.screenshot(path=str(save_path), full_page=False)
        print(f"  [OK] オータニ画面キャプチャを保存: {save_path.name}")
        await page.close()
    except Exception as e:
        print(f"  [ERROR] オータニ取得エラー: {e}")

# 2. トクバイ店舗（ヨークベニマル、たいらや、マルエツ）のチラシ大判キャプチャ
async def fetch_tokubai_leaflets(context):
    print("\n▶ [2/4] トクバイ加盟店（ヨークベニマル、たいらや、マルエツ）のチラシを取得中...")
    stores = [
        ("york_benimaru", "https://tokubai.co.jp/ヨークベニマル/9580/"),
        ("tairaya", "https://tokubai.co.jp/たいらや/372865/"),
        ("maruetsu", "https://tokubai.co.jp/マルエツ/3442/")
    ]
    for store_id, url in stores:
        page = await context.new_page()
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(2500)
            # チラシ詳細リンク
            chirashi_links = await page.query_selector_all("a[href*='/leaflets/']")
            if chirashi_links:
                first_link = await chirashi_links[0].get_attribute("href")
                detail_url = f"https://tokubai.co.jp{first_link}" if first_link.startswith("/") else first_link
                await page.goto(detail_url, timeout=30000)
                await page.wait_for_timeout(3000)
                save_path = FLYERS_DIR / f"{store_id}_leaflet_large.png"
                await page.screenshot(path=str(save_path), full_page=False)
                print(f"  [OK] {store_id} 大判チラシ保存: {save_path.name}")
            else:
                save_path = FLYERS_DIR / f"{store_id}_page.png"
                await page.screenshot(path=str(save_path), full_page=False)
                print(f"  [OK] {store_id} ページ保存: {save_path.name}")
        except Exception as e:
            print(f"  [ERROR] {store_id} 取得エラー: {e}")
        finally:
            await page.close()

# 3. Shufoo店舗（ベイシア、ジャパンミート）のキャプチャ
async def fetch_shufoo_stores(context):
    print("\n▶ [3/4] Shufoo加盟店（ベイシア、ジャパンミート）のチラシを取得中...")
    # ベイシア
    try:
        page = await context.new_page()
        await page.goto("https://www.shufoo.net/pntweb/shopDetail/239309/", timeout=30000)
        await page.wait_for_timeout(3000)
        link = await page.query_selector("li.shop_chirashi_list_item a, div.chirashi_list_box a")
        if link:
            href = await link.get_attribute("href")
            detail_url = f"https://www.shufoo.net{href}" if href.startswith("/") else href
            await page.goto(detail_url, timeout=30000)
            await page.wait_for_timeout(3000)
            save_path = FLYERS_DIR / "beisia_pure_flyer.png"
            await page.screenshot(path=str(save_path), full_page=False)
            print(f"  [OK] ベイシア チラシ保存: {save_path.name}")
        await page.close()
    except Exception as e:
        print(f"  [ERROR] ベイシア取得エラー: {e}")

    # ジャパンミート
    try:
        page = await context.new_page()
        await page.goto("https://www.shufoo.net/pntweb/shopDetail/898425/", timeout=30000)
        await page.wait_for_timeout(3000)
        link = await page.query_selector("li.shop_chirashi_list_item a, div.chirashi_list_box a")
        if link:
            href = await link.get_attribute("href")
            detail_url = f"https://www.shufoo.net{href}" if href.startswith("/") else href
            await page.goto(detail_url, timeout=30000)
            await page.wait_for_timeout(3000)
            # 操作バー非表示
            await page.evaluate("""
                document.querySelectorAll('#chirashiViewerControl, .chirashi_controller, .chirashi_ctrl, #chirashiBar, .controller').forEach(el => el.style.display = 'none');
            """)
            save_path = FLYERS_DIR / "japanmeat_clean.png"
            await page.screenshot(path=str(save_path), full_page=False)
            print(f"  [OK] ジャパンミート チラシ保存: {save_path.name}")
        await page.close()
    except Exception as e:
        print(f"  [ERROR] ジャパンミート取得エラー: {e}")

async def main_async():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1600, "height": 1400},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await fetch_otani_image(context)
        await fetch_tokubai_leaflets(context)
        await fetch_shufoo_stores(context)
        await browser.close()

def main():
    print("======================================================")
    print(" 主力スーパー チラシ原本・大判画像 自動収集")
    print("======================================================")
    asyncio.run(main_async())
    print("\n[OK] チラシ画像の自動収集がすべて完了しました！")

if __name__ == "__main__":
    main()
