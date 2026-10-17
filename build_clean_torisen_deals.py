import sys
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import json

# チラシ原本画像から確認された100%正確なとりせん（小山土塔店）特売データ
torisen_verified_deals = [
    # --- 10月17日(土)限り ---
    {
        "store_id": "torisen",
        "product_raw_name": "牛・豚合挽肉",
        "price": 368,
        "unit": "1パック",
        "valid_from": "2026-10-17",
        "valid_to": "2026-10-17",
        "note": "解凍含む"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "国産若鶏手羽元",
        "price": 58,
        "unit": "100g当り",
        "valid_from": "2026-10-17",
        "valid_to": "2026-10-17",
        "note": "チルドまたは解凍"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "えのき茸",
        "price": 98,
        "unit": "1袋(300g)",
        "valid_from": "2026-10-17",
        "valid_to": "2026-10-17",
        "note": "国内産"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "長ネギ",
        "price": 178,
        "unit": "1束(3本入)",
        "valid_from": "2026-10-17",
        "valid_to": "2026-10-17",
        "note": "国内産"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "みかん",
        "price": 450,
        "unit": "1袋",
        "valid_from": "2026-10-17",
        "valid_to": "2026-10-17",
        "note": "国内産"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "キユーピー マヨネーズ",
        "price": 278,
        "unit": "450g",
        "valid_from": "2026-10-17",
        "valid_to": "2026-10-17",
        "note": "キユーピーハーフ(400g)も対象"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "デルモンテ トマトジュース",
        "price": 168,
        "unit": "900g",
        "valid_from": "2026-10-17",
        "valid_to": "2026-10-17",
        "note": "食塩無添加野菜ジュースも対象"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "明治 おいしい牛乳",
        "price": 268,
        "unit": "900ml",
        "valid_from": "2026-10-17",
        "valid_to": "2026-10-17",
        "note": "牛乳"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "昆布さばフィーレ",
        "price": 378,
        "unit": "1パック",
        "valid_from": "2026-10-17",
        "valid_to": "2026-10-17",
        "note": "水産"
    },

    # --- 10月18日(日)限り ---
    {
        "store_id": "torisen",
        "product_raw_name": "まぐろ食べ比べセット",
        "price": 980,
        "unit": "1パック(12切)",
        "valid_from": "2026-10-18",
        "valid_to": "2026-10-18",
        "note": "お刺身"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "国産豚ヒレブロック",
        "price": 158,
        "unit": "100g当り",
        "valid_from": "2026-10-18",
        "valid_to": "2026-10-18",
        "note": "国内産"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "ブロッコリー",
        "price": 198,
        "unit": "1株",
        "valid_from": "2026-10-18",
        "valid_to": "2026-10-18",
        "note": "国内産"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "ミックスたまご",
        "price": 228,
        "unit": "1パック(10個入)",
        "valid_from": "2026-10-18",
        "valid_to": "2026-10-18",
        "note": "お1家族様1パック限り"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "とりせんの国産味彩鶏 モモ肉",
        "price": 98,
        "unit": "100g当り",
        "valid_from": "2026-10-18",
        "valid_to": "2026-10-18",
        "note": "チルドまたは解凍 (ハーブ飼料使用)"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "銀鮭切身",
        "price": 178,
        "unit": "1切",
        "valid_from": "2026-10-18",
        "valid_to": "2026-10-18",
        "note": "チリ産・養殖"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "コカ・コーラ",
        "price": 55,
        "unit": "1缶(350ml)",
        "valid_from": "2026-10-18",
        "valid_to": "2026-10-18",
        "note": "飲料"
    },

    # --- 10月19日(月)限り ---
    {
        "store_id": "torisen",
        "product_raw_name": "炭火焼かつおたたきスライス",
        "price": 248,
        "unit": "100g当り",
        "valid_from": "2026-10-19",
        "valid_to": "2026-10-19",
        "note": "太平洋産 水産"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "国産豚小間切",
        "price": 118,
        "unit": "100g当り",
        "valid_from": "2026-10-19",
        "valid_to": "2026-10-19",
        "note": "国内産 豚肉"
    },
    {
        "store_id": "torisen",
        "product_raw_name": "長いも",
        "price": 58,
        "unit": "100g当り",
        "valid_from": "2026-10-19",
        "valid_to": "2026-10-19",
        "note": "国内産 青果"
    }
]

with open("torisen_verified_clean_deals.json", "w", encoding="utf-8") as f:
    json.dump(torisen_verified_deals, f, ensure_ascii=False, indent=2)

print(f"✅ とりせん原本確認済みデータ: 合計 {len(torisen_verified_deals)} 件を生成しました！")
