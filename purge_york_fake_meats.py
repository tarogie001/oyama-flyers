import sys
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import sqlite3

conn = sqlite3.connect("deals.db")
c = conn.cursor()

# 削除前の該当レコードを確認
fake_ids = [1146, 1147, 1148, 1149, 1150]
c.execute(f"""
    SELECT id, store_id, product_raw_name, price, valid_from
    FROM flyer_deals
    WHERE id IN ({','.join(map(str, fake_ids))})
""")
rows = c.fetchall()
print("【削除対象の架空データ】:")
for r in rows:
    print(f"  ID: {r[0]}, 店舗: {r[1]}, 品名: {r[2]}, 価格: {r[3]}円, 日付: {r[4]}")

# 架空レコードを完全削除
c.execute(f"DELETE FROM flyer_deals WHERE id IN ({','.join(map(str, fake_ids))})")
conn.commit()
print(f"\n[OK] 架空データ {len(rows)} 件をデータベースから完全に抹消しました！")

# 削除後のヨークベニマル10/17レコードを確認
c.execute("""
    SELECT id, store_id, product_raw_name, price, valid_from
    FROM flyer_deals
    WHERE store_id = 'york_benimaru' AND valid_from = '2026-10-17'
""")
remaining = c.fetchall()
print("\n【残った正規データ (10/17)】:")
for r in remaining:
    print(f"  ID: {r[0]}, 品名: {r[2]}, 価格: {r[3]}円")

conn.close()
