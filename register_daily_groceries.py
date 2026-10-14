"""
register_daily_groceries.py
卵、牛乳、チーズ、ヨーグルト、納豆、即席ラーメン、カップラーメンの特売情報を登録
"""

import datetime
from deal_analyzer import DealAnalyzer

analyzer = DealAnalyzer()

# 基準日: 2026-10-14 (火)
deals = [
    # --- 卵 ---
    {"store_id": "beisia", "raw_name": "国内産 白玉たまご 10個入 (1点限り)", "price": 199, "unit": "1パック(10個)", "valid_from": "2026-10-14", "valid_to": "2026-10-14", "note": "本日限り特売！"},
    {"store_id": "tairaya", "raw_name": "こだわりたまご 10個入", "price": 198, "unit": "1パック(10個)", "valid_from": "2026-10-14", "valid_to": "2026-10-14", "note": "本日限り！"},
    {"store_id": "york_benimaru", "raw_name": "ミックスたまご 10個入 (1000円以上お買上げ)", "price": 188, "unit": "1パック(10個)", "valid_from": "2026-10-15", "valid_to": "2026-10-15", "note": "15日特売！"},
    {"store_id": "japanmeat", "raw_name": "国産赤玉たまご 10個入", "price": 218, "unit": "1パック(10個)", "valid_from": "2026-10-14", "valid_to": "2026-10-20", "note": "週間特売"},
    {"store_id": "otani", "raw_name": "赤玉たまご 10個入", "price": 268, "unit": "1パック(10個)", "valid_from": "2026-10-14", "valid_to": "2026-10-14", "note": "本日特売"},
    {"store_id": "maruetsu", "raw_name": "白玉たまご 10個入", "price": 228, "unit": "1パック(10個)", "valid_from": "2026-10-14", "valid_to": "2026-10-14", "note": "本日特売"},

    # --- 牛乳 ---
    {"store_id": "beisia", "raw_name": "毎日の食卓 牛乳 1000ml", "price": 188, "unit": "1本(1000ml)", "valid_from": "2026-10-15", "valid_to": "2026-10-15", "note": "15日限り"},
    {"store_id": "japanmeat", "raw_name": "農協牛乳 成分無調整 1000ml", "price": 189, "unit": "1本(1000ml)", "valid_from": "2026-10-14", "valid_to": "2026-10-20", "note": "週間特売"},
    {"store_id": "york_benimaru", "raw_name": "酪農牛乳 1000ml", "price": 198, "unit": "1本(1000ml)", "valid_from": "2026-10-15", "valid_to": "2026-10-15", "note": "15日特売"},
    {"store_id": "tairaya", "raw_name": "森永のおいしい牛乳 1000ml", "price": 218, "unit": "1本(1000ml)", "valid_from": "2026-10-14", "valid_to": "2026-10-14", "note": "本日限り！"},
    {"store_id": "otani", "raw_name": "雪印メグミルク 牛乳 1000ml", "price": 198, "unit": "1本(1000ml)", "valid_from": "2026-10-16", "valid_to": "2026-10-16", "note": "16日特売"},

    # --- 納豆 ---
    {"store_id": "japanmeat", "raw_name": "極小粒納豆 3パック", "price": 58, "unit": "1パック(3個)", "valid_from": "2026-10-14", "valid_to": "2026-10-20", "note": "今週最安値！"},
    {"store_id": "york_benimaru", "raw_name": "おかめ納豆 極小粒 3パック", "price": 78, "unit": "1パック(3個)", "valid_from": "2026-10-14", "valid_to": "2026-10-14", "note": "本日特売"},
    {"store_id": "beisia", "raw_name": "くめ納豆 丹精 3パック", "price": 78, "unit": "1パック(3個)", "valid_from": "2026-10-16", "valid_to": "2026-10-16", "note": "16日限り"},
    {"store_id": "otani", "raw_name": "おかめ納豆 極小粒 3パック", "price": 88, "unit": "1パック(3個)", "valid_from": "2026-10-14", "valid_to": "2026-10-14", "note": "本日特売"},
    {"store_id": "maruetsu", "raw_name": "金のつぶ パキッ！とたれ 3パック", "price": 78, "unit": "1パック(3個)", "valid_from": "2026-10-16", "valid_to": "2026-10-16", "note": "16日特売"},

    # --- ヨーグルト ---
    {"store_id": "japanmeat", "raw_name": "チチヤス ヨーグルト 4個パック", "price": 99, "unit": "1パック(4個)", "valid_from": "2026-10-14", "valid_to": "2026-10-20", "note": "今週最安値！"},
    {"store_id": "beisia", "raw_name": "森永 ビヒダス プレーンヨーグルト 400g", "price": 138, "unit": "1個(400g)", "valid_from": "2026-10-16", "valid_to": "2026-10-16", "note": "16日限り"},
    {"store_id": "otani", "raw_name": "明治 ブルガリアヨーグルト 400g", "price": 148, "unit": "1個(400g)", "valid_from": "2026-10-15", "valid_to": "2026-10-15", "note": "15日特売"},
    {"store_id": "maruetsu", "raw_name": "明治 ブルガリアヨーグルト 400g", "price": 158, "unit": "1個(400g)", "valid_from": "2026-10-15", "valid_to": "2026-10-15", "note": "15日特売"},
    {"store_id": "tairaya", "raw_name": "小岩井 生乳100%ヨーグルト 400g", "price": 188, "unit": "1個(400g)", "valid_from": "2026-10-15", "valid_to": "2026-10-15", "note": "15日特売"},

    # --- チーズ ---
    {"store_id": "beisia", "raw_name": "QBB スライスチーズ 7枚入", "price": 158, "unit": "1パック(7枚)", "valid_from": "2026-10-17", "valid_to": "2026-10-17", "note": "17日限り最安！"},
    {"store_id": "maruetsu", "raw_name": "雪印 とろけるスライスチーズ 7枚入", "price": 188, "unit": "1パック(7枚)", "valid_from": "2026-10-16", "valid_to": "2026-10-16", "note": "16日特売"},
    {"store_id": "tairaya", "raw_name": "雪印 6Pチーズ 108g", "price": 238, "unit": "1箱", "valid_from": "2026-10-16", "valid_to": "2026-10-16", "note": "16日特売"},
    {"store_id": "york_benimaru", "raw_name": "クラフト 切れてるチーズ 148g", "price": 258, "unit": "1箱", "valid_from": "2026-10-16", "valid_to": "2026-10-16", "note": "16日特売"},
    {"store_id": "otani", "raw_name": "雪印北海道100 とろけるチーズ 180g", "price": 298, "unit": "1袋", "valid_from": "2026-10-17", "valid_to": "2026-10-17", "note": "17日特売"},

    # --- 即席ラーメン ---
    {"store_id": "japanmeat", "raw_name": "サンヨー食品 サッポロ一番（各種 5食パック）", "price": 348, "unit": "1パック(5食)", "valid_from": "2026-10-14", "valid_to": "2026-10-20", "note": "週間最安値！"},
    {"store_id": "tairaya", "raw_name": "日清食品 マルちゃん正麺（各種 5食パック）", "price": 348, "unit": "1パック(5食)", "valid_from": "2026-10-17", "valid_to": "2026-10-17", "note": "17日特売"},
    {"store_id": "beisia", "raw_name": "サッポロ一番 5食パック", "price": 358, "unit": "1パック(5食)", "valid_from": "2026-10-14", "valid_to": "2026-10-14", "note": "本日特売"},
    {"store_id": "york_benimaru", "raw_name": "明星食品 チャルメラ（各種 5食パック）", "price": 328, "unit": "1パック(5食)", "valid_from": "2026-10-17", "valid_to": "2026-10-17", "note": "17日限り最安！"},
    {"store_id": "otani", "raw_name": "サッポロ一番 しょうゆ・みそ・塩 5食パック", "price": 398, "unit": "1パック(5食)", "valid_from": "2026-10-14", "valid_to": "2026-10-18", "note": "特売"},

    # --- カップラーメン ---
    {"store_id": "japanmeat", "raw_name": "日清 ごつ盛り カップラーメン 各種", "price": 98, "unit": "1個", "valid_from": "2026-10-14", "valid_to": "2026-10-20", "note": "今週最安値！"},
    {"store_id": "beisia", "raw_name": "東洋水産 赤いきつね・緑のたぬき 各種", "price": 108, "unit": "1個", "valid_from": "2026-10-15", "valid_to": "2026-10-15", "note": "15日限り"},
    {"store_id": "york_benimaru", "raw_name": "日清食品 どん兵衛 きつねうどん・天ぷらそば", "price": 128, "unit": "1個", "valid_from": "2026-10-17", "valid_to": "2026-10-17", "note": "17日特売"},
    {"store_id": "tairaya", "raw_name": "日清食品 カップヌードル（レギュラー・シーフード・カレー）", "price": 138, "unit": "1個", "valid_from": "2026-10-16", "valid_to": "2026-10-16", "note": "16日特売"},
    {"store_id": "otani", "raw_name": "日清 カップヌードル 各種", "price": 148, "unit": "1個", "valid_from": "2026-10-14", "valid_to": "2026-10-18", "note": "特売"}
]

count = 0
for d in deals:
    ok = analyzer.add_deal(
        d["store_id"], d["raw_name"], d["price"], d["unit"],
        d["valid_from"], d["valid_to"], d["note"]
    )
    if ok:
        count += 1

print(f"✅ 日配品・ラーメン等の特売データ {count} 件をデータベースに登録しました！")
