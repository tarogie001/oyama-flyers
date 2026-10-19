import sys
import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def check_shufoo(shop_id, store_name):
    url = f"https://www.shufoo.net/pntweb/shopDetail/{shop_id}/"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select("li.shop_chirashi_list_item, div.chirashi_list_box, .chirashi_box")
        print(f"\n【{store_name} (Shufoo: {shop_id})】")
        if not items:
            # 別のクラス名を探す
            links = [a for a in soup.find_all("a", href=True) if "/chirashi/" in a['href'] or "chirashi" in a['href']]
            print(f"  見つかったチラシ関連リンク: {len(links)}件")
            for l in links[:3]:
                print(f"  - {l.get_text(strip=True)[:40]} ({l['href']})")
        else:
            print(f"  掲載チラシ数: {len(items)}件")
            for it in items:
                title = it.get_text(separator=" ", strip=True)
                print(f"  - {title[:80]}")
    except Exception as e:
        print(f"【{store_name}】エラー: {e}")

def check_tokubai(shop_id, store_name):
    url = f"https://tokubai.co.jp/%E3%83%A4%E3%83%BC%E3%82%AF%E3%83%99%E3%83%8B%E3%83%9E%E3%83%AB/{shop_id}" if "ヨーク" in store_name else f"https://tokubai.co.jp/shops/{shop_id}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        leaflets = soup.select(".leaflet_box, .leaflet_item, a[href*='/leaflets/']")
        print(f"\n【{store_name} (トクバイ: {shop_id})】")
        print(f"  チラシリンク数: {len(leaflets)}件")
        seen = set()
        for l in leaflets:
            text = l.get_text(separator=" ", strip=True)
            href = l.get('href', '')
            if href and href not in seen:
                seen.add(href)
                print(f"  - {text[:60]} ({href})")
    except Exception as e:
        print(f"【{store_name}】エラー: {e}")

if __name__ == "__main__":
    check_shufoo("269396", "とりせん 小山土塔店")
    check_shufoo("898425", "ジャパンミート生鮮館 小山店")
    check_shufoo("239309", "ベイシア Foods Park 結城店")
    check_tokubai("9580", "ヨークベニマル 小山雨ヶ谷店")
