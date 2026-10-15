# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect("deals.db")
c = conn.cursor()
c.execute("UPDATE flyer_deals SET ingredient_name = 'チーズ' WHERE id = 707")
print(f"Updated cheese: {c.rowcount}")
conn.commit()
conn.close()
