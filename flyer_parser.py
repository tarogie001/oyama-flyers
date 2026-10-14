"""
flyer_parser.py
チラシ画像やテキストから特売情報を読み取り、データベースに登録するツール
"""

import os
import sys
import json
import re
import base64
import urllib.request
import urllib.error
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from deal_analyzer import DealAnalyzer

# Windows環境で文字化けを防ぐ設定
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
FLYERS_DIR = BASE_DIR / "flyers"
CONFIG_FILE = BASE_DIR / "config.json"


class FlyerParser:
    def __init__(self):
        self.analyzer = DealAnalyzer()
        FLYERS_DIR.mkdir(exist_ok=True)

    def import_from_text(self, text_lines: List[str], default_store_id: Optional[str] = None,
                         valid_days: int = 7) -> int:
        """
        テキストのメモや貼り付けから特売品を自動パースして登録する
        フォーマット例:
          - ヨークベニマル じゃがいも 98円 1袋
          - カワチ 納豆 58円 3パック
          - 豚バラうすぎり 128円 (store_id指定時)
        """
        today = datetime.date.today().isoformat()
        end_date = (datetime.date.today() + datetime.timedelta(days=valid_days)).isoformat()
        count = 0

        for line in text_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 価格（例: 98円、98）を抽出
            price_match = re.search(r"(\d+)\s*円?", line)
            if not price_match:
                continue
            price = int(price_match.group(1))

            # 店舗を特定
            store_id = default_store_id
            matched_store_name = ""
            for s in self.analyzer.stores:
                if s["chain"] in line or s["name"] in line or s["id"] in line:
                    store_id = s["id"]
                    matched_store_name = s["chain"]
                    break

            if not store_id:
                # 店舗が特定できない場合はスキップ
                print(f"⚠️ 店舗名が判定できませんでした: {line}")
                continue

            # 店舗名と価格部分を除去して商品名と単位を抽出
            cleaned_line = line
            if matched_store_name:
                cleaned_line = cleaned_line.replace(matched_store_name, "")
            cleaned_line = cleaned_line.replace(price_match.group(0), "").strip()

            # 単位（例: 1袋, 1玉, 100g, 2切, 3パック等）の判定
            unit_match = re.search(r"(\d+(?:g|kg|玉|袋|パック|切|尾|個|本|箱|食))", cleaned_line)
            unit = unit_match.group(1) if unit_match else ""
            if unit:
                cleaned_line = cleaned_line.replace(unit, "").strip()

            product_name = cleaned_line.strip() or "特売品"

            # 登録
            self.analyzer.add_deal(
                store_id=store_id,
                product_raw_name=product_name,
                price=price,
                unit=unit,
                valid_from=today,
                valid_to=end_date,
                note="テキストから取り込み"
            )
            count += 1
            print(f"✅ 登録完了: [{self.analyzer.store_dict[store_id]['chain']}] {product_name} {price}円 ({unit or '単位なし'})")

        return count

    def parse_flyer_image_with_gemini(self, image_path: Path, store_id: str,
                                      api_key: Optional[str] = None) -> int:
        """
        Gemini APIを利用してチラシ画像から食材と価格を抽出し、登録する
        """
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            print("⚠️ Gemini APIキーが設定されていません。")
            print("   環境変数 GEMINI_API_KEY を設定するか、config.json に記述してください。")
            return 0

        if not image_path.exists():
            print(f"❌ 画像ファイルが見つかりません: {image_path}")
            return 0

        print(f"🔍 チラシ画像をAIで解析中: {image_path.name} ...")

        # 画像をBase64エンコード
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "このスーパーまたは薬局のチラシ画像から、野菜、果物、肉類、魚類、納豆、ヨーグルト、"
            "調味料、インスタント麺、お菓子の特売品を抽出してください。\n"
            "必ず以下の形式のJSON配列のみを出力してください。\n"
            "[\n"
            "  {\"product\": \"商品名\", \"price\": 価格(整数), \"unit\": \"単位(例: 1袋, 100g等)\"}\n"
            "]"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        mime_type = "image/jpeg" if image_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as res:
                result = json.loads(res.read().decode("utf-8"))
                text_content = result["candidates"][0]["content"]["parts"][0]["text"]
                items = json.loads(text_content)

                today = datetime.date.today().isoformat()
                end_date = (datetime.date.today() + datetime.timedelta(days=6)).isoformat()
                added_count = 0

                for item in items:
                    p_name = item.get("product", "")
                    price = item.get("price", 0)
                    unit = item.get("unit", "")
                    if p_name and price > 0:
                        self.analyzer.add_deal(
                            store_id=store_id,
                            product_raw_name=p_name,
                            price=int(price),
                            unit=unit,
                            valid_from=today,
                            valid_to=end_date,
                            note="チラシ画像AI解析"
                        )
                        added_count += 1
                        print(f"  ・抽出成功: {p_name} {price}円 ({unit})")

                print(f"🎉 チラシ画像から {added_count} 件の特売品を登録しました！")
                return added_count
        except Exception as e:
            print(f"❌ AI画像解析エラー: {e}")
            return 0


def interactive_menu():
    parser = FlyerParser()
    print("========================================")
    print("   🛒 チラシ特売品 取り込みメニュー")
    print("========================================")
    print("1: メモ/テキストから貼り付けて一括登録")
    print("2: チラシ画像フォルダ（flyers/）を確認")
    print("3: 終了")
    print("----------------------------------------")
    choice = input("番号を選択してください (1-3): ").strip()

    if choice == "1":
        print("\n店舗名、商品名、価格を1行ずつ入力または貼り付けてください。")
        print("（入力完了時は空行でEnterを押してください）")
        print("例:\n  ヨークベニマル キャベツ 128円 1玉\n  カワチ 納豆 58円 3パック")
        print("----------------------------------------")
        lines = []
        while True:
            try:
                line = input()
                if not line.strip():
                    break
                lines.append(line)
            except EOFError:
                break
        if lines:
            count = parser.import_from_text(lines)
            print(f"\n合計 {count} 件を登録しました！")
        else:
            print("入力がありませんでした。")
    elif choice == "2":
        files = list(FLYERS_DIR.glob("*.*"))
        print(f"\n現在 flyers/ フォルダにあるファイル ({len(files)}件):")
        for f in files:
            print(f"・{f.name}")
        print("\n※ チラシ画像をここに入れておくと、AI解析で自動読み取りが可能です。")
    else:
        print("終了します。")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo-import":
        parser = FlyerParser()
        sample_text = [
            "たいらや にんじん 88円 1袋",
            "ジャパンミート 若鶏ささみ 58円 100g",
            "カワチ薬品 キットカット大袋 198円 1袋"
        ]
        parser.import_from_text(sample_text)
    else:
        interactive_menu()
