"""
deal_analyzer.py
小山市周辺のスーパー・薬局のチラシ特売データから、本日のお得な買い出しリストを分析・提案するツール
"""

import json
import sys
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

BASE_DIR = Path(__file__).resolve().parent
INGREDIENTS_FILE = BASE_DIR / "ingredients.json"
STORES_FILE = BASE_DIR / "stores.json"
DB_FILE = BASE_DIR / "deals.db"

# Windows環境で日本語や絵文字を文字化けなく出力するための設定
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class DealAnalyzer:
    def __init__(self):
        self.ingredients = self._load_json(INGREDIENTS_FILE)
        self.stores = self._load_json(STORES_FILE)
        self.store_dict = {s["id"]: s for s in self.stores}
        self._init_database()

    def _load_json(self, path: Path) -> Any:
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _init_database(self):
        """SQLiteデータベースとテーブルの初期化"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flyer_deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT NOT NULL,
                product_raw_name TEXT NOT NULL,
                category TEXT NOT NULL,
                ingredient_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                unit TEXT,
                valid_from TEXT NOT NULL,
                valid_to TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def match_ingredient(self, product_raw_name: str) -> Optional[Dict[str, str]]:
        """商品名から食材とカテゴリを自動判定"""
        name_lower = product_raw_name.lower()
        # 惣菜・加工品・調理済み品はお肉（精肉）から除外
        processed_food_keywords = ["お好み焼き", "おこのみやき", "ピザ", "コロッケ", "カツ", "フライ", "弁当", "惣菜", "串カツ", "ギョーザ", "餃子"]
        is_processed = any(kw in name_lower for kw in processed_food_keywords)

        for category, items in self.ingredients.items():
            if is_processed and "精肉" in category:
                continue
            for item in items:
                for kw in item.get("keywords", []):
                    if kw.lower() in name_lower:
                        return {
                            "category": category,
                            "ingredient_name": item["name"]
                        }
        return None

    def validate_deal_name(self, raw_name: str) -> bool:
        """不自然な合成文字列やOCR誤読ノイズを弾くバリデーション"""
        if not raw_name or len(raw_name) < 2:
            return False
        # 不完全・曖昧すぎる単語のみの商品名はツギハギ誤読として除外
        vague_names = ["いも", "こがね", "こま", "にく", "さかな"]
        if raw_name.strip() in vague_names:
            return False
        # 不自然な肉の部位混同（例: 豚肉とスティックなど）
        if "豚" in raw_name and "スティック" in raw_name:
            return False
        # チラシのボタンやUIノイズ
        if any(w in raw_name for w in ["チラシ", "クリック", "更新", "ページ", "セール", "全6枚", "全5枚", "全4枚"]):
            return False
        return True

    def add_deal(self, store_id: str, product_raw_name: str, price: int,
                 unit: str, valid_from: str, valid_to: str, note: str = "") -> bool:
        """特売品をデータベースに登録"""
        if not self.validate_deal_name(product_raw_name):
            return False

        match = self.match_ingredient(product_raw_name)
        category = match["category"] if match else "その他"
        ingredient_name = match["ingredient_name"] if match else product_raw_name

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO flyer_deals 
            (store_id, product_raw_name, category, ingredient_name, price, unit, valid_from, valid_to, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (store_id, product_raw_name, category, ingredient_name, price, unit, valid_from, valid_to, note))
        conn.commit()
        conn.close()
        return True

    def get_deals_for_date(self, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """指定日（デフォルトは本日）に有効な特売品一覧を取得"""
        if target_date is None:
            target_date = datetime.date.today().isoformat()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT store_id, product_raw_name, category, ingredient_name, price, unit, valid_from, valid_to, note
            FROM flyer_deals
            WHERE valid_from <= ? AND valid_to >= ?
            ORDER BY category, ingredient_name, price ASC
        """, (target_date, target_date))
        rows = cursor.fetchall()
        conn.close()

        deals = []
        for r in rows:
            store_info = self.store_dict.get(r[0], {"name": r[0], "chain": r[0]})
            deals.append({
                "store_id": r[0],
                "store_name": store_info["name"],
                "chain": store_info["chain"],
                "product_raw_name": r[1],
                "category": r[2],
                "ingredient_name": r[3],
                "price": r[4],
                "unit": r[5] or "",
                "valid_from": r[6],
                "valid_to": r[7],
                "note": r[8] or ""
            })
        return deals

    def generate_daily_report(self, target_date: Optional[str] = None) -> str:
        """本日のおすすめ買い出しレポート（LINE/メール用メッセージ）を生成"""
        if target_date is None:
            now = datetime.date.today()
            target_date = now.isoformat()
        else:
            now = datetime.date.fromisoformat(target_date)

        weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
        deals = self.get_deals_for_date(target_date)

        if not deals:
            return (
                f"【📅 {now.strftime('%Y年%m月%d日')}({weekday_jp}) 特売お知らせ】\n"
                f"現在、有効なチラシ特売データが登録されていません。\n"
                f"チラシデータを取り込んでお得情報を確認しましょう！"
            )

        # 食材ごとの最安値を集計
        best_deals_by_ingredient: Dict[str, Dict[str, Any]] = {}
        store_deal_counts: Dict[str, int] = {}

        for d in deals:
            ing = d["ingredient_name"]
            if ing not in best_deals_by_ingredient:
                best_deals_by_ingredient[ing] = d
                store_deal_counts[d["chain"]] = store_deal_counts.get(d["chain"], 0) + 1
            else:
                # 既に登録されているものより安い場合は更新
                if d["price"] < best_deals_by_ingredient[ing]["price"]:
                    best_deals_by_ingredient[ing] = d

        # カテゴリごとに分類
        categorized_deals: Dict[str, List[Dict[str, Any]]] = {}
        for d in best_deals_by_ingredient.values():
            cat = d["category"]
            categorized_deals.setdefault(cat, []).append(d)

        # 最もお得品が多い店舗（ハシゴ先おすすめ）
        top_stores = sorted(store_deal_counts.items(), key=lambda x: x[1], reverse=True)
        top_store_summary = "、".join([f"{name}({count}品)" for name, count in top_stores[:2]])

        # レポート文章の組み立て
        lines = [
            f"🛒【{now.strftime('%Y年%m月%d日')}({weekday_jp}) 本日の買い出しおすすめ】",
            "小山市周辺のチラシから厳選した最安・お得情報です！\n",
            "🌟 本日のおすすめ食材（最安値）",
            "--------------------------------"
        ]

        # カテゴリ表示順
        cat_order = [
            "野菜", "きのこ類", "季節の果物", "精肉（豚肉）", "精肉（鶏肉）",
            "魚介類", "日配品・大豆製品", "調味料", "麺類・インスタント", "お菓子", "その他"
        ]

        for cat in cat_order:
            if cat in categorized_deals:
                lines.append(f"【{cat}】")
                for item in categorized_deals[cat]:
                    unit_str = f" ({item['unit']})" if item['unit'] else ""
                    lines.append(
                        f"・{item['ingredient_name']}: {item['price']}円{unit_str} "
                        f"👉 {item['chain']}"
                    )
                lines.append("")

        lines.append("--------------------------------")
        if top_store_summary:
            lines.append(f"💡 本日の買い出しは【{top_store_summary}】を中心に行くと最もお得です！")

        return "\n".join(lines)


def load_demo_data():
    """小山市内のスーパー・薬局のサンプル特売データを投入（動作確認用）"""
    analyzer = DealAnalyzer()
    today = datetime.date.today().isoformat()
    end_of_week = (datetime.date.today() + datetime.timedelta(days=6)).isoformat()

    sample_deals = [
        # 野菜・きのこ
        ("york_benimaru", "茨城県産 じゃがいも 1箱/1袋", 98, "1袋", today, end_of_week),
        ("beisia", "群馬県産 キャベツ 1玉", 128, "1玉", today, end_of_week),
        ("torisen", "長野県産 えのきたけ", 58, "1袋", today, end_of_week),
        ("belc", "茨城県産 人参 1袋", 98, "1袋", today, end_of_week),
        ("otani", "長ネギ 1束(3本入)", 138, "1束", today, end_of_week),
        ("maruetsu", "福岡県産 ぶなしめじ", 78, "1パック", today, end_of_week),
        # 果物
        ("tairaya", "和歌山県産 みかん 1袋", 398, "1袋", today, end_of_week),
        ("york_benimaru", "長野県産 サンふじ りんご", 128, "1個", today, end_of_week),
        # お肉
        ("japanmeat", "国内産 豚バラうすぎり", 128, "100g", today, end_of_week),
        ("japanmeat", "国産 若鶏むね肉 特大パック", 48, "100g", today, end_of_week),
        ("trial", "若鶏もも肉", 78, "100g", today, end_of_week),
        ("tairaya", "豚もも切り落とし", 108, "100g", today, end_of_week),
        # お魚
        ("tairaya", "ノルウェー産 塩さば切身", 198, "2切", today, end_of_week),
        ("maruetsu", "チリ産 銀鮭切身", 258, "2切", today, end_of_week),
        # 日配・調味料・その他
        ("kawachi", "おかめ納豆 極小粒ミニ3", 58, "3パック", today, end_of_week),
        ("sugi", "明治ブルガリアヨーグルト", 128, "400g", today, end_of_week),
        ("kawachi", "ハウス バーモントカレー 230g", 148, "1箱", today, end_of_week),
        ("trial", "サッポロ一番 みそラーメン 5食パック", 298, "5食", today, end_of_week),
        ("belc", "カルビー ポテトチップス 各種", 88, "1袋", today, end_of_week)
    ]

    for item in sample_deals:
        analyzer.add_deal(
            store_id=item[0],
            product_raw_name=item[1],
            price=item[2],
            unit=item[3],
            valid_from=item[4],
            valid_to=item[5]
        )
    print(f"サンプル特売データ（{len(sample_deals)}件）を正常に登録しました！")


if __name__ == "__main__":
    import sys
    analyzer = DealAnalyzer()
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        load_demo_data()
    print("\n" + analyzer.generate_daily_report())
