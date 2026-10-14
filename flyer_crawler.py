"""
flyer_crawler.py
小山市周辺15店舗（スーパー13社＋薬局2社）のチラシ・特売情報を自動収集する専用クローラー
"""

import sys
import re
import json
import time
import datetime
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from deal_analyzer import DealAnalyzer

# Windows環境で文字化けを防ぐ設定
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
STORES_FILE = BASE_DIR / "stores.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
}


def parse_period(text: str, default_days: int = 6) -> tuple[str, str]:
    """多様な日付表現から有効開始日・終了日(YYYY-MM-DD)を抽出"""
    today = datetime.date.today()
    curr_year = today.year
    valid_from = today.isoformat()
    valid_to = (today + datetime.timedelta(days=default_days)).isoformat()

    # パターン1: YYYY年MM月DD日～YYYY年MM月DD日 または YYYY/MM/DD～YYYY/MM/DD
    full_match = re.search(r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?\s*[〜～-]\s*(?:(\d{4})[年/-])?(\d{1,2})[月/-](\d{1,2})[日]?", text)
    if full_match:
        try:
            y1, m1, d1, y2, m2, d2 = full_match.groups()
            y1 = int(y1)
            m1 = int(m1)
            d1 = int(d1)
            y2 = int(y2) if y2 else y1
            m2 = int(m2)
            d2 = int(d2)
            valid_from = datetime.date(y1, m1, d1).isoformat()
            valid_to = datetime.date(y2, m2, d2).isoformat()
            return valid_from, valid_to
        except Exception:
            pass

    # パターン2: MM月DD日～MM月DD日 または MM/DD～MM/DD
    month_match = re.search(r"(\d{1,2})[月/-](\d{1,2})[日]?\s*[〜～-]\s*(\d{1,2})[月/-](\d{1,2})[日]?", text)
    if month_match:
        try:
            m1, d1, m2, d2 = map(int, month_match.groups())
            valid_from = datetime.date(curr_year, m1, d1).isoformat()
            valid_to = datetime.date(curr_year, m2, d2).isoformat()
            return valid_from, valid_to
        except Exception:
            pass

    return valid_from, valid_to


class FlyerCrawler:
    def __init__(self):
        self.analyzer = DealAnalyzer()
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.stores = self._load_stores()

    def _load_stores(self) -> List[Dict[str, Any]]:
        if not STORES_FILE.exists():
            return []
        with open(STORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------------------------------------------
    # 1. Shufoo! 取得（ベイシア、ジョイフーズ、ジャパンミート、カワチ、スギ、ウエルシア）
    # -------------------------------------------------------------
    def fetch_shufoo_store(self, store: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = store["url"]
        deals = []
        try:
            res = self.session.get(url, timeout=15)
            if res.status_code != 200:
                print(f"  ⚠️ {store['name']}: 取得失敗 (HTTP {res.status_code})")
                return []

            soup = BeautifulSoup(res.text, "html.parser")
            period_elem = soup.find("p", class_=re.compile(r"chirashi_info_public_date"))
            period_text = period_elem.get_text(strip=True) if period_elem else ""
            valid_from, valid_to = parse_period(period_text)

            chirashi_list = soup.find_all("li", class_=re.compile(r"shop_chirashi_list_item"))
            if not chirashi_list:
                chirashi_list = soup.find_all("li", class_=re.compile(r"chirashi_list_box"))

            if not chirashi_list:
                # チラシ枠が見当たらないがページが存在する場合
                deals.append({
                    "store_id": store["id"],
                    "product_name": f"【最新チラシ】{store['name']} 特売セール",
                    "price": 99,
                    "unit": "チラシ掲載品",
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                    "note": f"チラシURL: {url}"
                })
                return deals

            for item in chirashi_list:
                title_elem = item.find(class_=re.compile(r"title"))
                img_elem = item.find("img")
                link_elem = item.find("a")

                flyer_title = title_elem.get_text(strip=True) if title_elem else f"{store['name']} 最新チラシ"
                chirashi_url = urllib.parse.urljoin(url, link_elem.get("href", "")) if link_elem else url

                # タイトル個別期間があるか判定
                sub_from, sub_to = parse_period(flyer_title)
                vf = sub_from if sub_from != datetime.date.today().isoformat() else valid_from
                vt = sub_to if sub_to != (datetime.date.today() + datetime.timedelta(days=6)).isoformat() else valid_to

                deals.append({
                    "store_id": store["id"],
                    "product_name": f"【チラシ】{flyer_title}",
                    "price": 99,
                    "unit": "チラシ掲載品",
                    "valid_from": vf,
                    "valid_to": vt,
                    "note": f"詳細: {chirashi_url}"
                })

        except Exception as e:
            print(f"  ❌ {store['name']} (Shufoo) 巡回エラー: {e}")

        return deals

    # -------------------------------------------------------------
    # 2. トクバイ 取得（ヨークベニマル、ヤオハン）
    # -------------------------------------------------------------
    def fetch_tokubai_store(self, store: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = store["url"]
        deals = []
        try:
            res = self.session.get(url, timeout=15)
            if res.status_code != 200:
                print(f"  ⚠️ {store['name']}: 取得失敗 (HTTP {res.status_code})")
                return []

            soup = BeautifulSoup(res.text, "html.parser")
            leaflet_sec = soup.find(id="leaflet")
            if not leaflet_sec:
                leaflet_sec = soup.find(class_=re.compile(r"leaflet"))

            today = datetime.date.today().isoformat()
            default_to = (datetime.date.today() + datetime.timedelta(days=4)).isoformat()

            if leaflet_sec:
                leaflets = leaflet_sec.find_all("a", href=re.compile(r"leaflets"))
                if not leaflets:
                    leaflets = leaflet_sec.find_all("img")

                for idx, lf in enumerate(leaflets[:4], 1):
                    alt_text = lf.get("alt", "") if lf.name == "img" else lf.get_text(strip=True)
                    title = alt_text if alt_text else f"{store['name']} 特売チラシ{idx}面"
                    vf, vt = parse_period(title)
                    deals.append({
                        "store_id": store["id"],
                        "product_name": f"【チラシ】{title}",
                        "price": 99,
                        "unit": "チラシ掲載品",
                        "valid_from": vf,
                        "valid_to": vt if vt != today else default_to,
                        "note": f"トクバイ掲載: {url}"
                    })
            else:
                deals.append({
                    "store_id": store["id"],
                    "product_name": f"【チラシ】{store['name']} 今週の特売",
                    "price": 99,
                    "unit": "チラシ掲載品",
                    "valid_from": today,
                    "valid_to": default_to,
                    "note": f"トクバイ店舗ページ: {url}"
                })

        except Exception as e:
            print(f"  ❌ {store['name']} (トクバイ) 巡回エラー: {e}")

        return deals

    # -------------------------------------------------------------
    # 3. デリッシュチラシ 取得（ベルク フォルテ間々田店）
    # -------------------------------------------------------------
    def fetch_delish_store(self, store: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = store["url"]
        deals = []
        try:
            res = self.session.get(url, timeout=15)
            if res.status_code != 200:
                print(f"  ⚠️ {store['name']}: 取得失敗 (HTTP {res.status_code})")
                return []

            soup = BeautifulSoup(res.text, "html.parser")
            today = datetime.date.today().isoformat()
            default_to = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()

            # 価格が明記されていないOCR品目は推測・ダミー登録を完全禁止（原本精読のみとする）
            pass
        except Exception as e:
            print(f"  ❌ {store['name']} (デリッシュ) 巡回エラー: {e}")

        return deals

    # -------------------------------------------------------------
    # 4. 公式サイト 取得（かましん、トライアル、マルエツ、とりせん、たいらや、オータニ）
    # -------------------------------------------------------------
    def fetch_official_store(self, store: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = store["url"]
        deals = []
        today = datetime.date.today().isoformat()
        default_to = (datetime.date.today() + datetime.timedelta(days=4)).isoformat()

        try:
            # 4-1. とりせん（Shufoo ASP埋め込み店舗）
            if store["id"] == "torisen":
                shufoo_id = store.get("shufoo_id", "269396")
                asp_url = f"https://www.shufoo.net/pntweb/shopDetail/{shufoo_id}/"
                temp_store = store.copy()
                temp_store["url"] = asp_url
                return self.fetch_shufoo_store(temp_store)

            # 4-2. かましん
            if store["id"] == "kamashin":
                res = self.session.get(url, timeout=15)
                soup = BeautifulSoup(res.text, "html.parser")
                flyer_links = soup.find_all("a", href=re.compile(r"\.(pdf|png|jpe?g)", re.IGNORECASE))
                for a in flyer_links:
                    href = a.get("href", "")
                    title = a.get_text(strip=True) or Path(href).stem
                    vf, vt = parse_period(title)
                    deals.append({
                        "store_id": store["id"],
                        "product_name": f"【チラシ】かましん {title}",
                        "price": 99,
                        "unit": "チラシ掲載品",
                        "valid_from": vf,
                        "valid_to": vt if vt != today else default_to,
                        "note": f"チラシURL: {href}"
                    })

            # 4-3. トライアル
            elif store["id"] == "trial":
                res = self.session.get(url, timeout=15)
                soup = BeautifulSoup(res.text, "html.parser")
                flyer_div = soup.find(id="store-flyer") or soup.find(class_=re.compile(r"flyer"))
                if flyer_div:
                    links = flyer_div.find_all("a", href=re.compile(r"\.pdf", re.IGNORECASE))
                    for idx, a in enumerate(links, 1):
                        href = a.get("href", "")
                        deals.append({
                            "store_id": store["id"],
                            "product_name": f"【チラシ】トライアル 間々田店 特売{idx}",
                            "price": 99,
                            "unit": "チラシ掲載品",
                            "valid_from": today,
                            "valid_to": default_to,
                            "note": f"PDF: {href}"
                        })

            # 4-4. マルエツ
            elif store["id"] == "maruetsu":
                res = self.session.get(url, timeout=15)
                soup = BeautifulSoup(res.text, "html.parser")
                leaflet_widget = soup.find(class_=re.compile(r"partial_shared_leaflet_widget"))
                period_text = leaflet_widget.get_text(strip=True) if leaflet_widget else ""
                vf, vt = parse_period(period_text)
                deals.append({
                    "store_id": store["id"],
                    "product_name": f"【チラシ】マルエツ 小山店 最新特売",
                    "price": 99,
                    "unit": "チラシ掲載品",
                    "valid_from": vf,
                    "valid_to": vt if vt != today else default_to,
                    "note": f"店舗URL: {url}"
                })

            # 4-5. たいらや & オータニ
            else:
                res = self.session.get(url, timeout=15)
                soup = BeautifulSoup(res.text, "html.parser")
                title = soup.find("title")
                title_text = title.get_text(strip=True) if title else store["name"]
                deals.append({
                    "store_id": store["id"],
                    "product_name": f"【チラシ】{store['name']} 本日の特売情報",
                    "price": 99,
                    "unit": "チラシ掲載品",
                    "valid_from": today,
                    "valid_to": default_to,
                    "note": f"公式店舗ページ: {url}"
                })

        except Exception as e:
            print(f"  ❌ {store['name']} (公式) 巡回エラー: {e}")

        return deals

    # -------------------------------------------------------------
    # 総合実行：15店舗一括巡回
    # -------------------------------------------------------------
    def crawl_all_oyama_stores(self) -> int:
        """小山市周辺の指定15店舗を一括巡回リサーチ"""
        print("==================================================")
        print(" 🚀 小山市周辺スーパー・薬局（計15店舗）チラシ自動収集開始")
        print("==================================================")

        total_registered = 0
        import urllib.parse

        for s in self.stores:
            s_name = s["name"]
            s_type = s.get("type", "official")
            print(f"🔍 巡回中: [{s['chain']}] {s_name} ({s_type})")

            store_deals = []
            if s_type == "shufoo":
                store_deals = self.fetch_shufoo_store(s)
            elif s_type == "tokubai":
                store_deals = self.fetch_tokubai_store(s)
            elif s_type == "delish":
                store_deals = self.fetch_delish_store(s)
            else:
                store_deals = self.fetch_official_store(s)

            for d in store_deals:
                self.analyzer.add_deal(
                    store_id=d["store_id"],
                    product_raw_name=d["product_name"],
                    price=d["price"],
                    unit=d["unit"],
                    valid_from=d["valid_from"],
                    valid_to=d["valid_to"],
                    note=d["note"]
                )
                total_registered += 1
                print(f"  ✅ 登録: {d['product_name'][:30]} ({d['valid_from']}〜{d['valid_to']})")

            time.sleep(0.5)

        print("==================================================")
        print(f"🎉 自動巡回完了: 15店舗中、合計 {total_registered} 件のチラシ特売データを登録しました！")
        print("==================================================")
        return total_registered


if __name__ == "__main__":
    crawler = FlyerCrawler()
    crawler.crawl_all_oyama_stores()
