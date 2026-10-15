# -*- coding: utf-8 -*-
"""
Delete hallucinated chimera items from deals.db:
- ID 713: いも (5kg, 250円)
- ID 708, 709, 710, 711: こがね (139円, 79円, 199円, 99円)
"""
import sqlite3

conn = sqlite3.connect("deals.db")
c = conn.cursor()

target_ids = [713, 708, 709, 710, 711]
c.execute(f"DELETE FROM flyer_deals WHERE id IN ({','.join(map(str, target_ids))})")
deleted_count = c.rowcount
conn.commit()
conn.close()

print(f"Deleted {deleted_count} hallucinated rows from deals.db")
