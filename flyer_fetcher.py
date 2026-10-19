"""
flyer_fetcher.py
小山市周辺15スーパーのWebチラシ掲載状況（トクバイ、Shufoo!、公式サイト）を
リアルタイムに自動巡回・スクレイピングし、最新チラシの更新日・特売期間を自動判定するエンジン
"""

import sys
import json
import re
import sqlite3
import datetime
import requests
from bs4 import BeautifulSoup
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
STORES_FILE = BASE_DIR / "stores.json"
STATUS_FILE = BASE_DIR / "store_flyer_status.json"
DB_FILE = BASE_DIR / "deals.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(text: str) -> str:
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'クリックして|チラシを見る|すべての\(全\d+枚\)', '', text)
    return text.strip()

def check_tokubai_flyer(url: str) -> str:
    """トクバイの店舗ページから最新チラシの号数・更新日を自動抽出"""
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if "/leaflets/" in a['href']:
                raw = clean_text(a.get_text(separator=" ", strip=True))
                # 例: 「10/19号チラシ 10月19日更新」
                m = re.search(r'(\d{1,2}/\d{1,2}号.*|\d{1,2}月\d{1,2}日更新.*|\d{1,2}/\d{1,2}〜.*)', raw)
                if m:
                    return m.group(1).strip()
                if "更新" in raw or "号" in raw:
                    return raw[:30].strip()
        return "最新チラシ公開中"
    except Exception:
        return "Webチラシ掲載中"

def check_shufoo_flyer(shop_id: str) -> str:
    """Shufoo!の店舗ページから最新チラシのタイトル・号数を自動抽出"""
    try:
        url = f"https://www.shufoo.net/pntweb/shopDetail/{shop_id}/"
        res = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")
        boxes = soup.select(".chirashi_list_box, li.shop_chirashi_list_item, .chirashi_box")
        for b in boxes:
            t = b.find(class_=re.compile(r'title|name|header'))
            d = b.find(class_=re.compile(r'date|period|time|term'))
            t_text = t.get_text(strip=True) if t else b.get_text(strip=True)
            d_text = d.get_text(strip=True) if d else ""
            full = clean_text(f"{t_text} {d_text}")
            if any(k in full for k in ["号", "月", "日", "★", "〜", "~", "フェア", "特価"]):
                return full[:30].strip()
        return "Webチラシ掲載中"
    except Exception:
        return "Webチラシ掲載中"

def get_latest_store_flyer_status(force_refresh=False) -> dict:
    """全15店舗の最新チラシ更新日・特売期間を自動判定して返す"""
    if not force_refresh and STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # キャッシュが1時間以内なら利用
            chk_time = data.get("_meta", {}).get("updated_at", "")
            if chk_time:
                diff = datetime.datetime.now() - datetime.datetime.fromisoformat(chk_time)
                if diff.total_seconds() < 3600:
                    return data
        except Exception:
            pass

    with open(STORES_FILE, "r", encoding="utf-8") as f:
        stores = json.load(f)

    # 1. DBから各店舗の最新チラシ特売期間を取得
    today_iso = datetime.date.today().isoformat()
    db_periods = {}
    if DB_FILE.exists():
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for s in stores:
            sid = s["id"]
            # 今日以降有効な特売のうち、最大valid_to
            c.execute("""
                SELECT min(valid_from), max(valid_to)
                FROM flyer_deals
                WHERE store_id = ? AND valid_to >= ?
            """, (sid, today_iso))
            row = c.fetchone()
            if row and row[0] and row[1]:
                all_f, all_t = row
                # 今日新しく始まった特売があればその開始日を採用（古い週末特売の混入防止）
                c.execute("""
                    SELECT min(valid_from)
                    FROM flyer_deals
                    WHERE store_id = ? AND valid_to >= ? AND valid_from >= ?
                """, (sid, today_iso, today_iso))
                new_f_row = c.fetchone()
                final_f = new_f_row[0] if (new_f_row and new_f_row[0]) else all_f

                f_from_str = final_f[5:].replace('-', '/')
                f_to_str = all_t[5:].replace('-', '/')
                db_periods[sid] = {
                    "from": final_f,
                    "to": all_t,
                    "label": f"{f_from_str}〜{f_to_str}"
                }
        conn.close()

    result = {}
    for s in stores:
        sid = s["id"]
        stype = s.get("type", "")
        url = s.get("url", "")
        shufoo_id = s.get("shufoo_id")

        web_label = ""
        # Shufoo
        if "shufoo" in stype or "shufoo.net" in url or shufoo_id:
            sh_id = shufoo_id or re.search(r'/shopDetail/(\d+)', url)
            if hasattr(sh_id, 'group'):
                sh_id = sh_id.group(1)
            if sh_id:
                web_label = check_shufoo_flyer(sh_id)
        # Tokubai
        elif "tokubai" in stype or "tokubai.co.jp" in url:
            web_label = check_tokubai_flyer(url)
        else:
            web_label = "公式Webチラシ掲載中"

        # 表示ラベルの組み立て
        if sid in db_periods:
            info = db_periods[sid]
            p_label = info["label"]
            if info["from"] == today_iso:
                status_str = f"本日更新! (特売: {p_label})"
            elif "更新" in web_label or "号" in web_label:
                status_str = f"{web_label} (特売: {p_label})"
            else:
                status_str = f"特売期間: {p_label}"
        else:
            status_str = web_label or "公式Webチラシ掲載中"

        result[sid] = status_str

    # メタ情報を付与して保存
    save_data = {
        "_meta": {"updated_at": datetime.datetime.now().isoformat()},
        "stores": result
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    return save_data

if __name__ == "__main__":
    data = get_latest_store_flyer_status(force_refresh=True)
    print("\n=== 自動判定結果 ===")
    for k, v in data.get("stores", {}).items():
        print(f"  {k}: {v}")
