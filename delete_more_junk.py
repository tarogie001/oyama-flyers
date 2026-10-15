# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect("deals.db")
c = conn.cursor()

ids = [640, 699, 712]
c.execute(f"DELETE FROM flyer_deals WHERE id IN ({','.join(map(str, ids))})")
print(f"Deleted {c.rowcount} rows")
conn.commit()
conn.close()
