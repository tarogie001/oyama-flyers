import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

flyers_dir = Path("flyers")
flyers_dir.mkdir(exist_ok=True)

stores = [
    ("tairaya", "https://tokubai.co.jp/たいらや/372865"),
    ("maruetsu", "https://tokubai.co.jp/マルエツ/3442"),
    ("york_benimaru", "https://tokubai.co.jp/ヨークベニマル/9580")
]

async def capture_tokubai():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for name, url in stores:
            print(f"Capturing Tokubai {name} ({url})...")
            context = await browser.new_context(
                viewport={"width": 1600, "height": 1800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(3000)
                
                # ページ全体のスクショ
                await page.screenshot(path=str(flyers_dir / f"{name}_tokubai.png"), full_page=False)
                print(f"[OK] Saved {name}_tokubai.png")

                # チラシ詳細リンクがあればクリックして原寸大チラシを取得
                chirashi_links = await page.query_selector_all("a[href*='/leaflets/']")
                if chirashi_links:
                    first_link = await chirashi_links[0].get_attribute("href")
                    detail_url = f"https://tokubai.co.jp{first_link}" if first_link.startswith("/") else first_link
                    print(f"Opening leaflet: {detail_url}")
                    p2 = await context.new_page()
                    await p2.goto(detail_url, timeout=30000)
                    await p2.wait_for_timeout(3000)
                    await p2.screenshot(path=str(flyers_dir / f"{name}_leaflet_large.png"), full_page=False)
                    print(f"[OK] Saved {name}_leaflet_large.png")
                    await p2.close()
            except Exception as e:
                print(f"[ERROR] {name}: {e}")
            finally:
                await page.close()
                await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_tokubai())
