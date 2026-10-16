# -*- coding: utf-8 -*-
"""
Register verified flyer deals into flyer_deals table in deals.db.
Only deals with 100% verified visual proof from downloaded flyer images are added.
"""
import sys
import sqlite3

# Windows環境で文字化け・絵文字エラーを防ぐ設定
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

VERIFIED_DEALS = [
    # --- オータニ チラシ原本確認済み ---
    {
        "store_id": "otani",
        "product_raw_name": "サンヨー食品 サッポロ一番（みそ・塩・しょうゆ 5食パック）",
        "category": "麺類・インスタント",
        "ingredient_name": "即席ラーメン",
        "price": 328,
        "unit": "1袋(5食)",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-14",
        "note": "お一人様いずれか1袋限り"
    },
    {
        "store_id": "otani",
        "product_raw_name": "タカノフーズ CGC極小粒納豆 (50g×3)",
        "category": "日配品・大豆製品",
        "ingredient_name": "納豆",
        "price": 98,
        "unit": "1パック",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": ""
    },
    {
        "store_id": "otani",
        "product_raw_name": "明治 おいしい牛乳 (900ml)",
        "category": "日配品・大豆製品",
        "ingredient_name": "牛乳",
        "price": 268,
        "unit": "1本",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": ""
    },
    # --- マルエツ チラシ原本確認済み (10/15限り) ---
    {
        "store_id": "maruetsu",
        "product_raw_name": "アメリカ産など 銀だら切身（解凍）",
        "category": "魚介類",
        "ingredient_name": "たら",
        "price": 269,
        "unit": "100g当り",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": "木曜限り"
    },
    {
        "store_id": "maruetsu",
        "product_raw_name": "銀だら西京漬",
        "category": "魚介類",
        "ingredient_name": "たら",
        "price": 680,
        "unit": "1パック(2切入)",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": "木曜限り"
    },
    {
        "store_id": "maruetsu",
        "product_raw_name": "国産 若どりささみ",
        "category": "精肉（鶏肉）",
        "ingredient_name": "鶏ささみ",
        "price": 98,
        "unit": "100g当り",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": "木曜限り"
    },
    {
        "store_id": "maruetsu",
        "product_raw_name": "長野県産 えのき茸",
        "category": "きのこ類",
        "ingredient_name": "えのき",
        "price": 129,
        "unit": "1袋",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": "木曜限り"
    },
    # --- ジャパンミート チラシ原本確認済み (10/14〜10/16 大感謝祭) ---
    {
        "store_id": "japanmeat",
        "product_raw_name": "ブラジル産・解凍品 豚バラブロック",
        "category": "精肉（豚肉）",
        "ingredient_name": "豚バラブロック",
        "price": 129,
        "unit": "100g当り",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": "エブリデイ・ロープライス"
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "豪・ブラジル産・国産（解凍・解凍品） 豚鶏合挽LL",
        "category": "精肉（豚肉）",
        "ingredient_name": "豚挽肉",
        "price": 79,
        "unit": "100g当り",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": "エブリデイ・ロープライス"
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "国産豚 小間スライスL (1kgパック)",
        "category": "精肉（豚肉）",
        "ingredient_name": "豚こま切れ肉",
        "price": 890,
        "unit": "1パック(1kg)",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": "100g当り89円"
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "シマダヤ わが家の一杯 生ラーメン 3食（醤油・味噌・塩 各110g×3）",
        "category": "麺類・インスタント",
        "ingredient_name": "生ラーメン",
        "price": 159,
        "unit": "1袋(3食)",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": ""
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "森永 ビヒダスヨーグルト 4P（各種）",
        "category": "日配品・大豆製品",
        "ingredient_name": "ヨーグルト",
        "price": 139,
        "unit": "1パック",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": ""
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "アメリカ産（解凍） 銀鱈切身",
        "category": "魚介類",
        "ingredient_name": "たら",
        "price": 698,
        "unit": "4切",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": ""
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "三陸産他（養殖） 国産 甘塩銀鮭",
        "category": "魚介類",
        "ingredient_name": "鮭",
        "price": 698,
        "unit": "4切",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": ""
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "ノルウェー産他（解凍） 生アトランティックサーモン（刺身用）",
        "category": "魚介類",
        "ingredient_name": "鮭",
        "price": 430,
        "unit": "100g当り",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": ""
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "中国産他 つぼぬきいか",
        "category": "魚介類",
        "ingredient_name": "いか",
        "price": 555,
        "unit": "4杯",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": ""
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "北海道産などの国内産 れんこん",
        "category": "野菜",
        "ingredient_name": "れんこん",
        "price": 79,
        "unit": "100g当り",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": ""
    },
    {
        "store_id": "japanmeat",
        "product_raw_name": "青森県産などの国内産 ごぼう",
        "category": "野菜",
        "ingredient_name": "ごぼう",
        "price": 199,
        "unit": "2本入・1袋",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-16",
        "note": ""
    },
    # --- ベイシア チラシ原本確認済み (10/14〜10/20) ---
    {
        "store_id": "beisia",
        "product_raw_name": "青森などの国内産 りんご",
        "category": "季節の果物",
        "ingredient_name": "りんご",
        "price": 129,
        "unit": "1コ",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-14",
        "note": "10/14限り"
    },
    {
        "store_id": "beisia",
        "product_raw_name": "北海道などの国内産 じゃがいも・玉ねぎ・人参 よりどり3点",
        "category": "野菜",
        "ingredient_name": "ジャガイモ",
        "price": 99,
        "unit": "3点",
        "valid_from": "2026-10-14",
        "valid_to": "2026-10-14",
        "note": "10/14限り"
    },
    {
        "store_id": "beisia",
        "product_raw_name": "生寿司一品各種（まぐろづくし・サーモンづくしなど）",
        "category": "魚介類",
        "ingredient_name": "まぐろ",
        "price": 500,
        "unit": "1パック",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": "10/15限り"
    },
    {
        "store_id": "beisia",
        "product_raw_name": "北海道産他 秋鮭切身（養殖）",
        "category": "魚介類",
        "ingredient_name": "鮭",
        "price": 249,
        "unit": "100g当り",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": "10/15限り"
    },
    {
        "store_id": "beisia",
        "product_raw_name": "アメリカ・カナダまたはメキシコ産 豚肉こま切れ",
        "category": "精肉（豚肉）",
        "ingredient_name": "豚こま切れ肉",
        "price": 79,
        "unit": "100g当り",
        "valid_from": "2026-10-16",
        "valid_to": "2026-10-16",
        "note": "10/16限り"
    },
    {
        "store_id": "beisia",
        "product_raw_name": "中国など 骨取り塩さば",
        "category": "魚介類",
        "ingredient_name": "さば",
        "price": 500,
        "unit": "1パック(4枚)",
        "valid_from": "2026-10-16",
        "valid_to": "2026-10-16",
        "note": "10/16限り"
    },
    {
        "store_id": "beisia",
        "product_raw_name": "ベイシア 太陽の恵み(白) 1パック(10コ入)",
        "category": "日配品・大豆製品",
        "ingredient_name": "卵",
        "price": 259,
        "unit": "1パック(10コ入)",
        "valid_from": "2026-10-20",
        "valid_to": "2026-10-20",
        "note": "10/20限り お一人様1パック限り"
    },
    # --- ヨークベニマル チラシ原本確認済み (10/12〜10/21) ---
    {
        "store_id": "york_benimaru",
        "product_raw_name": "セブンプレミアム 毎日の食卓牛乳 (1000ml)",
        "category": "日配品・大豆製品",
        "ingredient_name": "牛乳",
        "price": 208,
        "unit": "1本",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-21",
        "note": "ヨークベニマル定番特売"
    },
    {
        "store_id": "york_benimaru",
        "product_raw_name": "おかめ仕立て 旨味極小粒納豆 (3パック)",
        "category": "日配品・大豆製品",
        "ingredient_name": "納豆",
        "price": 98,
        "unit": "1パック(3個入)",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": "10/15限り"
    },
    {
        "store_id": "york_benimaru",
        "product_raw_name": "明治 ブルガリアヨーグルト (400g)",
        "category": "日配品・大豆製品",
        "ingredient_name": "ヨーグルト",
        "price": 148,
        "unit": "1個",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-15",
        "note": "10/15限り"
    },
    {
        "store_id": "york_benimaru",
        "product_raw_name": "国産 豚肉こま切れ",
        "category": "精肉（豚肉）",
        "ingredient_name": "豚こま切れ肉",
        "price": 108,
        "unit": "100g当り",
        "valid_from": "2026-10-15",
        "valid_to": "2026-10-18",
        "note": "厳選特価"
    },
    # --- たいらや チラシ原本確認済み (10/12〜10/16) ---
    {
        "store_id": "tairaya",
        "product_raw_name": "国産 若鶏もも肉",
        "category": "精肉（鶏肉）",
        "ingredient_name": "鶏もも肉",
        "price": 98,
        "unit": "100gあたり",
        "valid_from": "2026-10-12",
        "valid_to": "2026-10-16",
        "note": "ザ・鶏の市"
    },
    {
        "store_id": "tairaya",
        "product_raw_name": "北海道（その他国内）産 にんじん <M> 3本入",
        "category": "野菜",
        "ingredient_name": "ニンジン",
        "price": 138,
        "unit": "1袋",
        "valid_from": "2026-10-12",
        "valid_to": "2026-10-16",
        "note": ""
    },
    {
        "store_id": "tairaya",
        "product_raw_name": "青森・宮城県産他 生さば",
        "category": "魚介類",
        "ingredient_name": "さば",
        "price": 398,
        "unit": "1パック",
        "valid_from": "2026-10-12",
        "valid_to": "2026-10-16",
        "note": ""
    },
    {
        "store_id": "tairaya",
        "product_raw_name": "福島県（その他国内）産 生しいたけ <量り売り>",
        "category": "きのこ類",
        "ingredient_name": "しいたけ",
        "price": 128,
        "unit": "100gあたり",
        "valid_from": "2026-10-16",
        "valid_to": "2026-10-16",
        "note": "10/16限り"
    },
    {
        "store_id": "tairaya",
        "product_raw_name": "カナダ産 豚バラ肉超うす切り",
        "category": "精肉（豚肉）",
        "ingredient_name": "豚バラ（うすぎり）",
        "price": 198,
        "unit": "100gあたり",
        "valid_from": "2026-10-16",
        "valid_to": "2026-10-16",
        "note": "10/16限り"
    },
    {
        "store_id": "tairaya",
        "product_raw_name": "チリ産 サーモントラウト ブロック <養殖・生食用または加熱用>",
        "category": "魚介類",
        "ingredient_name": "鮭",
        "price": 298,
        "unit": "100gあたり",
        "valid_from": "2026-10-16",
        "valid_to": "2026-10-16",
        "note": "10/16限り"
    }
]

def main():
    conn = sqlite3.connect("deals.db")
    c = conn.cursor()

    # 2. 原本確認済み【100%本物データ】のみを新規登録（既存重複はスキップ）
    inserted_count = 0
    for d in VERIFIED_DEALS:
        c.execute("""
            SELECT id FROM flyer_deals 
            WHERE store_id = ? AND product_raw_name = ? AND valid_from = ?
        """, (d["store_id"], d["product_raw_name"], d["valid_from"]))
        if c.fetchone():
            continue

        c.execute("""
            INSERT INTO flyer_deals (store_id, product_raw_name, category, ingredient_name, price, unit, valid_from, valid_to, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d["store_id"],
            d["product_raw_name"],
            d["category"],
            d["ingredient_name"],
            d["price"],
            d["unit"],
            d["valid_from"],
            d["valid_to"],
            d["note"]
        ))
        inserted_count += 1
        print(f"追加: {d['store_id']} - {d['product_raw_name']} ({d['price']}円)")
            
    conn.commit()
    conn.close()
    print(f"\n完了: {inserted_count} 件のチラシ原本確認済みデータを登録しました。")

if __name__ == "__main__":
    main()
