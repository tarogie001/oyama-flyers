"""
auto_gemini_crawler.py
最新のチラシ画像を Gemini 1.5 Flash (Vision) で自動解析し、特売品を deals.db に自律登録するスクリプト
（GitHub Actions および ローカル共通）
"""

import os
import sys
import json
import datetime
import time
from pathlib import Path
from gemini_flyer_parser import analyze_flyer_with_gemini
from deal_analyzer import DealAnalyzer

BASE_DIR = Path(__file__).resolve().parent
FLYERS_DIR = BASE_DIR / "flyers"

def run_ai_analysis():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[INFO] GEMINI_API_KEY が未設定のため、AI画像解析ステップはスキップします。")
        return

    print("======================================================")
    print("🤖 Google Gemini AI によるチラシ画像自律解析を開始します")
    print("======================================================")

    analyzer = DealAnalyzer()
    today_str = datetime.date.today().isoformat()

    # 解析対象のチラシ画像リスト
    tasks = [
        {"store_id": "beisia", "store_name": "ベイシア", "images": ["beisia_pure_flyer.png"]},
        {"store_id": "japanmeat", "store_name": "ジャパンミート", "images": ["japanmeat_clean.png"]},
        {"store_id": "york_benimaru", "store_name": "ヨークベニマル", "images": ["york_benimaru_leaflet_large.png", "york_benimaru_leaflet_sub1.png"]},
        {"store_id": "tairaya", "store_name": "たいらや", "images": ["tairaya_leaflet_large.png"]},
        {"store_id": "maruetsu", "store_name": "マルエツ", "images": ["maruetsu_leaflet_large.png"]},
        {"store_id": "otani", "store_name": "オータニ", "images": ["otani_flyer_orig.jpg"]}
    ]

    total_added = 0
    for task in tasks:
        store_id = task["store_id"]
        store_name = task["store_name"]

        # 存在する画像をすべて取得（ベニマルの日替わり＋週間など複数枚対応）
        target_imgs = []
        for img_name in task["images"]:
            p = FLYERS_DIR / img_name
            if p.exists() and p.stat().st_size > 5000:
                target_imgs.append(p)

        if not target_imgs:
            print(f"[-] {store_name}: 解析対象の画像が見つかりません")
            continue

        for target_img in target_imgs:
            print(f"\n▶ {store_name} のチラシ画像 ({target_img.name}) を Gemini AI に送信中...")
            deals = analyze_flyer_with_gemini(target_img, store_name, base_date=today_str)

            if deals:
                count = 0
                for item in deals:
                    raw_name = item.get("raw_name") or item.get("ingredient") or ""
                    price = item.get("price")
                    unit = item.get("unit") or "1個"
                    v_from = item.get("valid_from") or today_str
                    v_to = item.get("valid_to") or v_from
                    note = item.get("note") or ""

                    if raw_name and price and isinstance(price, (int, float)) and price > 0:
                        ok = analyzer.add_deal(store_id, raw_name, int(price), unit, v_from, v_to, note)
                        if ok:
                            count += 1
                print(f"✅ {store_name} ({target_img.name}): AIが読み取った {count} 件の特売品を登録しました！")
                total_added += count
            else:
                print(f"[-] {store_name} ({target_img.name}): 今回はAI抽出結果がありませんでした")

            # レート制限回避のクールダウン
            time.sleep(20)

    print(f"\n🎉 AI画像解析が完了しました（合計 {total_added} 件の特売品を新規登録/更新）")

if __name__ == "__main__":
    run_ai_analysis()
