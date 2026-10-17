import sys
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import sqlite3

conn = sqlite3.connect("deals.db")
c = conn.cursor()

c.execute("SELECT id, store_id, product_raw_name, price, unit, valid_from, valid_to FROM flyer_deals ORDER BY store_id, valid_from")
rows = c.fetchall()
print(f"現在DBに残っている特売データ全件: {len(rows)} 件\n")

# 店舗別・日付別の内訳
grouped = {}
for r in rows:
    key = (r[1], r[5])
    grouped.setdefault(key, []).append(r)

for (store, v_from), items in sorted(grouped.items()):
    print(f"--- {store} [{v_from}] ({len(items)}件) ---")
    for it in items[:5]:
        print(f"  [{it[0]}] {it[2]} -> {it[3]}円 ({it[4]})")
    if len(items) > 5:
        print(f"  ... 他 {len(items)-5} 件")

conn.close()
