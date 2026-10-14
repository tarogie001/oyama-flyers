# -*- coding: utf-8 -*-
"""
Apply user-verified fixes to deals.db:
1. ID 736: Update ingredient_name of Nature Megumi from '牛乳' to 'ヨーグルト'
2. ID 570: Update date of Beisia Koukun from '2026-10-15' to '2026-10-14' (yesterday only)
3. ID 684: Delete hallucinated Beisia lettuce 129 deal
"""
import sqlite3

conn = sqlite3.connect("deals.db")
c = conn.cursor()

# 1. ナチュレ恵 -> ヨーグルト
c.execute("UPDATE flyer_deals SET ingredient_name = 'ヨーグルト' WHERE id = 736")
print(f"ナチュレ恵 (ID 736) をヨーグルトに更新: {c.rowcount} 件")

# 2. ベイシア 香薫 -> 2026-10-14
c.execute("UPDATE flyer_deals SET valid_from = '2026-10-14', valid_to = '2026-10-14' WHERE id = 570")
print(f"ベイシア 香薫 (ID 570) を 2026-10-14 に更新: {c.rowcount} 件")

# 3. 架空のレタス 129円 削除
c.execute("DELETE FROM flyer_deals WHERE id = 684")
print(f"架空レタス (ID 684) を削除: {c.rowcount} 件")

conn.commit()
conn.close()
print("✅ deals.db のデータ修正が完了しました。")
