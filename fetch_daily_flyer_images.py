"""
fetch_daily_flyer_images.py
主力スーパー全店舗の最新チラシ原本・高解像度画像を自動収集・保存するスクリプト
（GitHub Actionsおよびローカル共通）
"""

import sys
import re
import datetime
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
    print("\n▶ [1/3] オータニの最新チラシ原本画像を取得中...")
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
    print("\n▶ [2/3] トクバイ加盟店（ヨークベニマル、たいらや、マルエツ）のチラシを取得中...")
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
            chirashi_links = await page.query_selector_all("a[href*='/leaflets/']")
            unique_hrefs = []
            for link_el in chirashi_links:
                href = await link_el.get_attribute("href")
                if href:
                    clean_href = href.split("?")[0]
                    if re.search(r'/leaflets/\d+', clean_href):
                        if clean_href not in [u.split("?")[0] for u in unique_hrefs]:
                            unique_hrefs.append(href)

            if unique_hrefs:
                for idx, target_href in enumerate(unique_hrefs[:2]):
                    detail_url = f"https://tokubai.co.jp{target_href}" if target_href.startswith("/") else target_href
                    try:
                        await page.goto(detail_url, timeout=30000)
                        await page.wait_for_timeout(3000)
                        suffix = "_large" if idx == 0 else f"_sub{idx}"
                        save_path = FLYERS_DIR / f"{store_id}_leaflet{suffix}.png"
                        await page.screenshot(path=str(save_path), full_page=False)
                        print(f"  [OK] {store_id} チラシ画像保存 ({idx+1}枚目): {save_path.name}")
                    except Exception as ex:
                        print(f"  [WARN] {store_id} チラシ({idx+1}枚目)取得失敗: {ex}")
            else:
                save_path = FLYERS_DIR / f"{store_id}_page.png"
                await page.screenshot(path=str(save_path), full_page=False)
                print(f"  [OK] {store_id} ページ保存: {save_path.name}")
        except Exception as e:
            print(f"  [ERROR] {store_id} 取得エラー: {e}")
        finally:
            await page.close()

# 3. Shufoo店舗（ベイシア、ジャパンミート、とりせん）の高解像度キャプチャ
async def fetch_shufoo_stores(context):
    print("\n▶ [3/3] Shufoo加盟店（ベイシア、ジャパンミート、とりせん）のチラシを取得中...")
    stores = [
        ("beisia", "239309", "beisia_pure_flyer.png"),
        ("japanmeat", "898425", "japanmeat_clean.png"),
        ("torisen", "269396", "torisen_clean.png")
    ]
    for store_id, shop_id, out_name in stores:
        try:
            page = await context.new_page()
            await page.goto(f"https://www.shufoo.net/pntweb/shopDetail/{shop_id}/", timeout=30000)
            await page.wait_for_timeout(3000)
            links = await page.query_selector_all("li.shop_chirashi_list_item a, div.chirashi_list_box a")
            unique_hrefs = []
            for l in links:
                h = await l.get_attribute("href")
                if h and h not in unique_hrefs:
                    unique_hrefs.append(h)

            if unique_hrefs:
                for idx, href in enumerate(unique_hrefs[:2]):
                    detail_url = f"https://www.shufoo.net{href}" if href.startswith("/") else href
                    sub_page = await context.new_page()
                    try:
                        await sub_page.goto(detail_url, timeout=30000)
                        await sub_page.wait_for_timeout(3500)
                        await sub_page.evaluate("""
                            document.querySelectorAll('#chirashiViewerControl, .chirashi_controller, .chirashi_ctrl, #chirashiBar, .controller, header, footer, div[class*="toolbar"], div[class*="control"], div[class*="navi"], #header, #footer, .shop_header, .detail_info_box').forEach(el => el.style.setProperty('display', 'none', 'important'));
                        """)
                        target_name = out_name if idx == 0 else out_name.replace(".png", f"_sub{idx}.png")
                        save_path = FLYERS_DIR / target_name
                        area = await sub_page.query_selector("#chirashi-area, #chirashiViewer, #chirashi_img, .chirashi_view, div.viewer")
                        if area:
                            await area.screenshot(path=str(save_path))
                        else:
                            await sub_page.screenshot(path=str(save_path), full_page=False)
                        print(f"  [OK] {store_id} 高解像度チラシ保存 ({idx+1}枚目): {save_path.name}")
                    finally:
                        await sub_page.close()
            else:
                save_path = FLYERS_DIR / out_name
                await page.screenshot(path=str(save_path), full_page=False)
                print(f"  [WARN] {store_id} チラシリンク見つからず全画面保存: {save_path.name}")
            await page.close()
        except Exception as e:
            print(f"  [ERROR] {store_id} 取得エラー: {e}")

async def main_async():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1600, "height": 1800},
            device_scale_factor=2,
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
