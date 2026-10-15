# -*- coding: utf-8 -*-
"""
Register verified flyer deals into flyer_deals table in deals.db.
Only deals with 100% verified visual proof from downloaded flyer images are added.
"""
import sqlite3

VERIFIED_DEALS = [
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
    }
]

def main():
    conn = sqlite3.connect("deals.db")
    c = conn.cursor()
    
    inserted_count = 0
    for d in VERIFIED_DEALS:
        # Check duplicate
        c.execute("""
            SELECT id FROM flyer_deals 
            WHERE store_id = ? AND product_raw_name = ? AND valid_from = ?
        """, (d["store_id"], d["product_raw_name"], d["valid_from"]))
        row = c.fetchone()
        if not row:
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
        else:
            print(f"既存スキップ: {d['store_id']} - {d['product_raw_name']}")
            
    conn.commit()
    conn.close()
    print(f"\n完了: {inserted_count} 件のチラシ原本確認済みデータを登録しました。")

if __name__ == "__main__":
    main()
