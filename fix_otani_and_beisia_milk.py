# -*- coding: utf-8 -*-
"""
Apply verified fixes to deals.db:
1. Update Otani Sapporo Ichiban valid dates to 2026-10-14 (yesterday only)
2. Delete Beisia phantom milk deal (ID 689)
"""
import sqlite3

conn = sqlite3.connect("deals.db")
c = conn.cursor()

# 1. オータニ サッポロ一番 -> 2026-10-14
c.execute("""
    UPDATE flyer_deals 
    SET valid_from = '2026-10-14', valid_to = '2026-10-14' 
    WHERE store_id = 'otani' AND product_raw_name LIKE '%サッポロ一番%'
""")
print(f"オータニ サッポロ一番を 2026-10-14 に更新: {c.rowcount} 件")

# 2. ベイシア 架空牛乳 (ID 689) 削除
c.execute("DELETE FROM flyer_deals WHERE id = 689")
print(f"ベイシア 架空牛乳 (ID 689) を削除: {c.rowcount} 件")

conn.commit()
conn.close()
print("deals.db のデータ修正が完了しました。")
