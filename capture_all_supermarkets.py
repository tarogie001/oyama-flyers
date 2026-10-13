import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import urllib.parse

flyers_dir = Path("flyers")
flyers_dir.mkdir(exist_ok=True)

async def capture_store(name, url, filename_prefix, evaluate_js=None):
    print(f"\n=== Capturing {name} ({url}) ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1600, "height": 1400},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # 操作バー等の消去スクリプトがあれば実行
            if evaluate_js:
                await page.evaluate(evaluate_js)

            # スクリーンショット
            save_path = flyers_dir / f"{filename_prefix}.png"
            await page.screenshot(path=str(save_path), full_page=False)
            print(f"[OK] Saved: {save_path}")
        except Exception as e:
            print(f"[ERROR] Error {name}: {e}")
        finally:
            await browser.close()

async def main():
    # 1. ジャパンミート (操作ボタン非表示)
    js_hide_controls = """
    document.querySelectorAll('#chirashiViewerControl, .chirashi_controller, .chirashi_ctrl, #chirashiBar, .controller').forEach(el => el.style.display = 'none');
    """
    await capture_store(
        "ジャパンミート",
        "https://www.shufoo.net/pntweb/shopDetail/898425/17094052370725/",
        "japanmeat_clean",
        js_hide_controls
    )

    # 2. ヨークベニマル小山雨ヶ谷店 (トクバイ)
    await capture_store(
        "ヨークベニマル",
        "https://tokubai.co.jp/ヨークベニマル/9580/",
        "york_benimaru_page"
    )

    # 3. たいらや粟宮店
    await capture_store(
        "たいらや",
        "https://tokubai.co.jp/たいらや/20120/",
        "tairaya_page"
    )

    # 4. マルエツ小山店
    await capture_store(
        "マルエツ",
        "https://www.maruetsu.co.jp/chirashi/search/detail.php?shop_cd=0402",
        "maruetsu_page"
    )

if __name__ == "__main__":
    asyncio.run(main())
