"""
weekly_planner.py
1週間全体のチラシ特売スケジュールを分析し、
「今日買うべき食材」と「後日安くなるので待つべき食材」を判定して提案する週間最適化エンジン
"""

import sys
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Windows環境で文字化けを防ぐ設定
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
INGREDIENTS_FILE = BASE_DIR / "ingredients.json"
STORES_FILE = BASE_DIR / "stores.json"
DB_FILE = BASE_DIR / "deals.db"


class WeeklyPlanner:
    def __init__(self):
        self.ingredients = self._load_json(INGREDIENTS_FILE)
        self.stores = self._load_json(STORES_FILE)
        self.store_dict = {s["id"]: s for s in self.stores}

    def _load_json(self, path: Path) -> Any:
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_week_range(self, base_date: Optional[datetime.date] = None) -> tuple[datetime.date, datetime.date]:
        """基準日を含む週（月曜日〜日曜日）の開始日と終了日を取得"""
        if base_date is None:
            base_date = datetime.date.today()
        # 月曜日
        start_of_week = base_date - datetime.timedelta(days=base_date.weekday())
        # 日曜日
        end_of_week = start_of_week + datetime.timedelta(days=6)
        return start_of_week, end_of_week

    def analyze_weekly_plan(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        1週間の特売データを横断分析し、
        ・今日買うべき食材 (buy_today)
        ・後日に回すべき食材 (wait_for_later)
        ・週間スケジュール (weekly_schedule)
        を算出する
        """
        if target_date is None:
            today_date = datetime.date.today()
        else:
            today_date = datetime.date.fromisoformat(target_date)

        today_str = today_date.isoformat()
        start_week, end_week = self.get_week_range(today_date)
        start_str = start_week.isoformat()
        end_str = end_week.isoformat()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # 今週に重なる特売をすべて取得
        cursor.execute("""
            SELECT store_id, product_raw_name, category, ingredient_name, price, unit, valid_from, valid_to, note
            FROM flyer_deals
            WHERE valid_to >= ? AND valid_from <= ?
            ORDER BY price ASC
        """, (start_str, end_str))
        rows = cursor.fetchall()
        conn.close()

        # 食材ごとに全期間の特売をまとめる
        ingredient_deals: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            ing_name = r[3]
            # チラシのボタン文言やノイズを除外
            if not ing_name or "チラシ" in ing_name or "見る" in ing_name or "更新" in ing_name or "セール" in ing_name:
                continue
            if r[2] == "その他" and ("全" in ing_name or "枚" in ing_name):
                continue
            store_info = self.store_dict.get(r[0], {"name": r[0], "chain": r[0]})
            d = {
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
            }
            ingredient_deals.setdefault(d["ingredient_name"], []).append(d)

        buy_today = []
        wait_for_later = []
        weekly_schedule: Dict[str, List[Dict[str, Any]]] = {}

        for ing_name, deals in ingredient_deals.items():
            # 今週の全体最安値
            deals_sorted = sorted(deals, key=lambda x: x["price"])
            best_deal_in_week = deals_sorted[0]

            # 今日の特売（本日有効なもの）
            today_deals = [d for d in deals if d["valid_from"] <= today_str <= d["valid_to"]]
            best_deal_today = min(today_deals, key=lambda x: x["price"]) if today_deals else None

            # 判定ロジック
            if best_deal_today:
                if best_deal_today["price"] <= best_deal_in_week["price"]:
                    # 今日が週間最安値！
                    is_today_only = (best_deal_today["valid_to"] == today_str)
                    buy_today.append({
                        "ingredient": ing_name,
                        "raw_name": best_deal_today.get("product_raw_name", ing_name),
                        "category": best_deal_today["category"],
                        "price": best_deal_today["price"],
                        "unit": best_deal_today["unit"],
                        "store": best_deal_today["chain"],
                        "store_id": best_deal_today["store_id"],
                        "is_today_only": is_today_only,
                        "note": "本日限り！" if is_today_only else "今週最安値"
                    })
                else:
                    # 今日買えるが、後日もっと安くなる！
                    future_deals = [d for d in deals if d["valid_from"] > today_str and d["price"] < best_deal_today["price"]]
                    if future_deals:
                        target_future = min(future_deals, key=lambda x: x["price"])
                        f_date = datetime.date.fromisoformat(target_future["valid_from"])
                        f_weekday = ["月", "火", "水", "木", "金", "土", "日"][f_date.weekday()]
                        wait_for_later.append({
                            "ingredient": ing_name,
                            "category": best_deal_today["category"],
                            "today_price": best_deal_today["price"],
                            "future_price": target_future["price"],
                            "unit": target_future["unit"],
                            "future_store": target_future["chain"],
                            "future_day": f"{f_date.strftime('%m/%d')}({f_weekday})",
                            "diff": best_deal_today["price"] - target_future["price"]
                        })

            # 週間スケジュール用（最安値の日に割り振り）
            best_start = datetime.date.fromisoformat(best_deal_in_week["valid_from"])
            best_end = datetime.date.fromisoformat(best_deal_in_week["valid_to"])
            
            # 過ぎた日の特売（今日より前に終わったもの）は除外！
            if best_end < today_date:
                continue

            # 表示用ラベル（今日以前から有効なものは今日付け、未来のものはその開始日）
            display_date = max(best_start, today_date)
            b_weekday = ["月", "火", "水", "木", "金", "土", "日"][display_date.weekday()]
            day_key = f"{display_date.strftime('%m/%d')}({b_weekday})"
            weekly_schedule.setdefault(day_key, []).append(best_deal_in_week)

        # 食材ごとに「今日以降で最安になる購入日・店舗」を算出
        best_buy_schedule = []
        for ing_name, deals in ingredient_deals.items():
            valid_deals = [d for d in deals if datetime.date.fromisoformat(d["valid_to"]) >= today_date]
            if not valid_deals:
                continue
            # 今日以降で最安値
            cheapest = min(valid_deals, key=lambda x: x["price"])
            c_start = datetime.date.fromisoformat(cheapest["valid_from"])
            c_end = datetime.date.fromisoformat(cheapest["valid_to"])
            
            # 最安日ラベルの算出
            is_best_today = (c_start <= today_date <= c_end)
            if is_best_today:
                if c_end == today_date:
                    best_day_label = f"本日 {today_date.strftime('%m/%d')} 限り！"
                    advice = "本日が今週の底値！今日中に買いましょう"
                else:
                    best_day_label = f"本日〜{c_end.strftime('%m/%d')}まで"
                    advice = "現在底値！今日買ってもOKです"
            else:
                w_jp = ["月", "火", "水", "木", "金", "土", "日"][c_start.weekday()]
                best_day_label = f"{c_start.strftime('%m/%d')}({w_jp})から"
                advice = f"{c_start.strftime('%m/%d')}の特売開始まで待機推奨"

            best_buy_schedule.append({
                "ingredient": ing_name,
                "raw_name": cheapest.get("product_raw_name", ing_name),
                "category": cheapest["category"],
                "best_price": cheapest["price"],
                "unit": cheapest["unit"],
                "store": cheapest["chain"],
                "store_id": cheapest["store_id"],
                "store_name": cheapest["store_name"],
                "best_day_label": best_day_label,
                "is_best_today": is_best_today,
                "advice": advice,
                "sort_date": max(c_start, today_date).isoformat()
            })

        # 最安日が近い順（今日最安のものを上に）ソート
        best_buy_schedule.sort(key=lambda x: (0 if x["is_best_today"] else 1, x["sort_date"], x["best_price"]))

        return {
            "today": today_date,
            "buy_today": buy_today,
            "wait_for_later": wait_for_later,
            "weekly_schedule": weekly_schedule,
            "best_buy_schedule": best_buy_schedule
        }

    def generate_optimized_report(self, target_date: Optional[str] = None) -> str:
        """1週間の仕入れ計画に基づいた本日のおすすめ提案メッセージを生成"""
        plan = self.analyze_weekly_plan(target_date)
        today = plan["today"]
        weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][today.weekday()]

        lines = [
            f"🛒【{today.strftime('%Y年%m月%d日')}({weekday_jp}) 本日の週間仕入れ最適化提案】",
            "小山市のチラシから1週間の最安値を分析し、今日のアクションを計算しました！\n"
        ]

        # 1. 今日買うべき食材
        lines.append("🔥【今日買うべき食材（今週最安値・今日が買い時！）】")
        lines.append("--------------------------------------------------")
        if plan["buy_today"]:
            for item in plan["buy_today"]:
                unit_str = f" ({item['unit']})" if item['unit'] else ""
                badge = " ⚡[本日限り特売]" if item['is_today_only'] else " ★[今週最安]"
                lines.append(
                    f"・{item['ingredient']}: {item['price']}円{unit_str} 👉 {item['store']}{badge}"
                )
        else:
            lines.append("・本日急いで買うべき食材はありません（後日の特売をお待ちください）")
        lines.append("")

        # 2. 今日は買わずに待つべき食材
        lines.append("⏳【今日は買わずに待つべき食材（後日さらに安くなります！）】")
        lines.append("--------------------------------------------------")
        if plan["wait_for_later"]:
            for item in plan["wait_for_later"]:
                unit_str = f" ({item['unit']})" if item['unit'] else ""
                lines.append(
                    f"・{item['ingredient']}: 今日 {item['today_price']}円 👉 "
                    f"【{item['future_day']} に {item['future_store']} で {item['future_price']}円{unit_str}】になるため待機推奨（{item['diff']}円お得！）"
                )
        else:
            lines.append("・後日に安くなる見送り推奨品はありません")
        lines.append("")

        # 3. 本日のチラシ目玉特売なし（平常価格の日常食材）
        lines.append("ℹ️【本日のチラシ目玉特売なし（店頭通常価格の日常食材）】")
        lines.append("--------------------------------------------------")
        featured_ings = {it['ingredient'] for it in plan['buy_today']} | {it['ingredient'] for it in plan['wait_for_later']}
        staple_candidates = ["キャベツ", "白菜", "大根", "ほうれんそう", "ブロッコリー", "レタス", "豚バラ（うすぎり）", "鶏もも肉"]
        no_deal_staples = [ing for ing in staple_candidates if ing not in featured_ings]
        if no_deal_staples:
            lines.append(f"・{', '.join(no_deal_staples)} など（※本日はチラシ目玉特売がないため、平常価格での購入または特売日をお待ちください）")
        lines.append("")

        # 4. 今週の仕入れスケジュール
        lines.append("📅【今週の賢い仕入れスケジュール（週間ルート）】")
        lines.append("--------------------------------------------------")
        for day, items in sorted(plan["weekly_schedule"].items()):
            store_summary = {}
            for it in items:
                store_summary.setdefault(it["chain"], []).append(it["ingredient_name"])
            stores_text = " / ".join([f"{st}: {', '.join(ings[:3])}" for st, ings in store_summary.items()])
            lines.append(f"・{day}: {stores_text}")

        lines.append("--------------------------------------------------")
        lines.append("💡 今日仕入れるべき店舗を中心に回り、待機推奨品は後日の特売日に仕入れましょう！")

        return "\n".join(lines)

    def export_json_data(self, target_date: Optional[str] = None, output_path: Optional[Path] = None) -> Path:
        """Androidアプリ向けにチラシ直リンク・特売情報をJSON形式で出力"""
        if output_path is None:
            output_path = BASE_DIR / "latest_deals.json"

        plan = self.analyze_weekly_plan(target_date)

        # チラシ特売なし日常食材
        featured_ings = {it['ingredient'] for it in plan['buy_today']} | {it['ingredient'] for it in plan['wait_for_later']}
        staple_candidates = ["キャベツ", "白菜", "大根", "ほうれんそう", "ブロッコリー", "レタス"]
        no_deal_staples = [ing for ing in staple_candidates if ing not in featured_ings]

        # 店舗ごとにチラシリンクをマッピング
        store_map = {}
        for s in self.stores:
            store_map[s["id"]] = {
                "id": s["id"],
                "chain": s["chain"],
                "name": s["name"],
                "url": s["url"],
                "type": s.get("type", "official")
            }

        # buy_today に店舗のチラシURLを付与
        enriched_buy_today = []
        for item in plan["buy_today"]:
            s_info = None
            for s in self.stores:
                if s["chain"] == item["store"] or s["id"] == item.get("store_id"):
                    s_info = s
                    break
            enriched_buy_today.append({
                **item,
                "store_name": s_info["name"] if s_info else item["store"],
                "flyer_url": s_info["url"] if s_info else ""
            })

        # weekly_schedule にも店舗チラシURLを付与
        enriched_weekly = {}
        for day_k, d_items in plan["weekly_schedule"].items():
            enriched_items = []
            for item in d_items:
                s_info = None
                for s in self.stores:
                    if s["chain"] == item.get("chain") or s["id"] == item.get("store_id"):
                        s_info = s
                        break
                enriched_items.append({
                    **item,
                    "store_name": s_info["name"] if s_info else item.get("chain", ""),
                    "flyer_url": s_info["url"] if s_info else ""
                })
            enriched_weekly[day_k] = enriched_items

        # best_buy_schedule にも店舗チラシURLを付与
        enriched_best_buy = []
        for item in plan["best_buy_schedule"]:
            s_info = None
            for s in self.stores:
                if s["chain"] == item.get("store") or s["id"] == item.get("store_id"):
                    s_info = s
                    break
            enriched_best_buy.append({
                **item,
                "store_name": s_info["name"] if s_info else item.get("store_name", item["store"]),
                "flyer_url": s_info["url"] if s_info else ""
            })

        try:
            from zoneinfo import ZoneInfo
            now_jst = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        except Exception:
            now_jst = datetime.datetime.now()

        export_data = {
            "updated_at": now_jst.strftime("%Y-%m-%d %H:%M"),
            "target_date": plan["today"].isoformat(),
            "target_date_label": plan["today"].strftime("%Y年%m月%d日"),
            "buy_today": enriched_buy_today,
            "wait_for_later": plan["wait_for_later"],
            "no_deal_staples": no_deal_staples,
            "weekly_schedule": enriched_weekly,
            "best_buy_schedule": enriched_best_buy,
            "stores": self.stores
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"📱 アプリ用データを出力しました: {output_path.name}")
        return output_path


def load_weekly_demo_data():
    """1週間の特売スケジュールをリアルにシミュレートしたサンプルデータ投入"""
    from deal_analyzer import DealAnalyzer
    analyzer = DealAnalyzer()
    today = datetime.date.today()
    t_str = today.isoformat()

    # 月曜(今日)、火曜(明日)、水曜、金曜、土日の特売
    t_plus_1 = (today + datetime.timedelta(days=1)).isoformat()
    t_plus_2 = (today + datetime.timedelta(days=2)).isoformat()
    t_plus_3 = (today + datetime.timedelta(days=3)).isoformat()
    t_plus_4 = (today + datetime.timedelta(days=4)).isoformat()
    t_plus_6 = (today + datetime.timedelta(days=6)).isoformat()

    sample_schedule = [
        # 月曜日（今日）最安
        ("york_benimaru", "茨城県産 じゃがいも 1袋", 98, "1袋", t_str, t_plus_2),
        ("tairaya", "ノルウェー産 塩さば切身 2切", 198, "2切", t_str, t_str), # 本日限り！
        ("kawachi", "ハウス バーモントカレー 230g", 148, "1箱", t_str, t_plus_6),

        # 今日は高いが、火曜（明日）にベイシアでキャベツが超特価！
        ("maruetsu", "キャベツ 1玉", 158, "1玉", t_str, t_plus_2), # 今日のキャベツ
        ("beisia", "群馬県産 キャベツ 1玉 [火曜市]", 98, "1玉", t_plus_1, t_plus_2), # 明日の最安キャベツ

        # 今日は高いが、水曜日にジャパンミートでお肉大特売！
        ("tairaya", "国内産 豚バラうすぎり", 148, "100g", t_str, t_plus_1), # 今日の豚肉
        ("japanmeat", "国内産 豚バラうすぎり [水曜肉の日]", 98, "100g", t_plus_2, t_plus_3), # 水曜最安豚肉
        ("japanmeat", "国産 若鶏むね肉 特大パック", 45, "100g", t_plus_2, t_plus_3),

        # 今日は普通だが、金曜日にカワチ薬品で納豆特売！
        ("trial", "おかめ納豆 極小粒ミニ3", 68, "3パック", t_str, t_plus_6), # 今日の納豆
        ("kawachi", "おかめ納豆 極小粒ミニ3 [金曜薬品市]", 54, "3パック", t_plus_4, t_plus_6), # 金曜最安納豆

        # 週末特売
        ("torisen", "長野県産 ぶなしめじ", 68, "1パック", t_plus_4, t_plus_6)
    ]

    for item in sample_schedule:
        analyzer.add_deal(
            store_id=item[0],
            product_raw_name=item[1],
            price=item[2],
            unit=item[3],
            valid_from=item[4],
            valid_to=item[5],
            note="週間特売スケジュール"
        )
    print(f"✅ 1週間の特売スケジュールデータ（{len(sample_schedule)}件）を登録しました！")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        load_weekly_demo_data()
    planner = WeeklyPlanner()
    print("\n" + planner.generate_optimized_report())
