"""
gemini_flyer_parser.py
Google Gemini API (Vision) を活用し、チラシ画像から日替わり特売品を100%自律的に抽出するモジュール
"""

import os
import sys
import json
import base64
import datetime
import time
import io
from PIL import Image
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

BASE_DIR = Path(__file__).resolve().parent

# .env ファイルがあれば読み込む
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    os.environ["GEMINI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

_CACHED_MODELS = None

def get_active_gemini_models(api_key: str) -> List[str]:
    """Google APIに問い合わせて、利用可能なGeminiモデルの優先リストを動的生成"""
    global _CACHED_MODELS
    if _CACHED_MODELS:
        return _CACHED_MODELS

    try:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        res = requests.get(list_url, timeout=10)
        if res.status_code == 200:
            models = res.json().get("models", [])
            supported = [
                m["name"].replace("models/", "")
                for m in models
                if "generateContent" in m.get("supportedGenerationMethods", [])
                and not any(x in m["name"].lower() for x in ["tts", "embedding", "aqa", "imagen"])
            ]
            print(f"[INFO] 🤖 Google公式APIから利用可能モデル一覧を取得しました ({len(supported)}件)")

            # 画像解析に対応したモデルの中で安定版を優先ソート
            # 1. 安定版指定 (1.5-flash-002, 1.5-flash-001)
            # 2. 最新エイリアス (1.5-flash-latest, 2.0-flash)
            # 3. その他の flash / pro
            def sort_key(name: str) -> int:
                n = name.lower()
                # 誤読を防ぐため LITE は完全排除し、高精度な通常 Flash モデルを優先
                if "lite" in n or "tts" in n or "clip" in n: return 99
                if "flash-latest" in n: return 0
                if "3.5-flash" in n: return 1
                if "3.8-flash" in n: return 2
                if "flash" in n and "preview" not in n: return 3
                return 10

            sorted_models = sorted(supported, key=sort_key)
            # 上位2候補を動的採用
            _CACHED_MODELS = sorted_models[:2]
            print(f"[INFO] 🤖 採用モデル優先順位: {_CACHED_MODELS}")
            return _CACHED_MODELS
    except Exception as e:
        print(f"[WARN] モデル一覧の自動取得に失敗したため既定リストを使用: {e}")

    _CACHED_MODELS = ["gemini-flash-latest", "gemini-3.5-flash"]
    return _CACHED_MODELS

def analyze_flyer_with_gemini(image_path: Path, store_name: str, base_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """チラシ画像をGemini最新モデルに送信し、特売品リストをJSON配列として取得"""
    if not GEMINI_API_KEY:
        print("[WARN] GEMINI_API_KEY が設定されていません。スキップします。")
        return []

    if not image_path.exists():
        print(f"[WARN] 画像ファイルが存在しません: {image_path}")
        return []

    if not base_date:
        base_date = datetime.date.today().isoformat()

    # 安全ガード：解像度が低すぎる画像（短辺600px未満または横1000px未満）は文字潰れによる捏造（ハルシネーション）の原因となるため解析を拒絶・スキップ
    try:
        with Image.open(image_path) as check_img:
            w, h = check_img.size
            if w < 1000 or h < 600:
                print(f"[REJECT] 🛡️ 安全ガード作動: {store_name} の画像解像度が低すぎます ({w}x{h})。文字潰れによる架空データ捏造（ハルシネーション）を防止するため解析をスキップします。")
                return []
    except Exception as e:
        print(f"[WARN] 画像サイズ確認失敗: {e}")

    # 画像を文字鮮明度を保ったまま最適サイズ・JPEGに自動軽量化（3MB -> 300~500KB）
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            max_dimension = 1400
            if max(img.width, img.height) > max_dimension:
                scale = max_dimension / max(img.width, img.height)
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80, optimize=True)
            img_bytes = buf.getvalue()
    except Exception as e:
        print(f"[WARN] 画像の最適化に失敗したため生データを読み込みます: {e}")
        with open(image_path, "rb") as f:
            img_bytes = f.read()

    b64_img = base64.b64encode(img_bytes).decode("utf-8")
    mime_type = "image/jpeg"

    prompt = f"""
あなたはスーパーのチラシ解析の最高峰エキスパートです。
画像は「{store_name}」のチラシ（またはその一部）です。
本日の基準日付は「{base_date}」です。

このチラシ画像に実際に掲載されている【野菜】【きのこ】【果物】【精肉（豚・鶏・牛）】【鮮魚・水産】、および【卵・牛乳・チーズ・ヨーグルト・納豆】【即席ラーメン・カップラーメン】の日替わり特売品を正確に読み取り、JSON配列形式で抽出してください。

【厳格な遵守ルール】
1. 【文字の完全一致厳守（一文字たりとも創作・すり替えの禁止）】:
   raw_name には、チラシ画像に実際に印字されている日本語（漢字・カタカナ・ひらがな）を一文字ずつそのまま書き写してください。
   画像にない漢字や単語（例: 画像に「銀だら」とあるのに「真だら鍋用」と書く、画像に「銀鱈」とあるのに「殻付帆立」と書く、画像に「りんご」とあるのに「レタス」と書く等）を創作・すり替えることは絶対に禁止します。
   文字が100%確実に読めない商品は、一切出力せず完全にスキップ（除外）してください。
2. 【枠線・罫線の厳守（ツギハギ合成の完全禁止）】:
   異なる枠線（罫線）をまたいで離れた位置にある商品名・規格・価格（例: お米の「5kg」と別枠の調味料の数字や野菜の文字）を勝手にツギハギ合成することは絶対に禁止します。1つの商品枠内に確実にまとまっている情報のみを抽出してください。「いも」「こがね」「こま」等の不完全な短縮単語は抽出せず、正式な品名を抽出してください。
3. 【日付ヘッダーの照合義務】:
   各商品は、その商品が掲載されている枠の真上または周囲にある「◯月◯日限り」「◯日〜◯日」などの日付見出しヘッダーを必ず目視確認し、その日付を valid_from / valid_to に設定してください。隣の列や別の日の枠と混同してはいけません。
4. 価格（price）は「税抜（本体）価格」を整数値で出力してください。税込しか書かれていない場合は税込価格を整数で出力してください。
5. 惣菜、お弁当、お酒、ペット用品などは除外し、日常の食卓食材（生鮮食品、卵、牛乳、乳製品・チーズ、納豆、豆腐、即席麺類）を中心に抽出してください。

【出力フォーマット（JSON形式）】
[
  {{
    "ingredient": "食材の大分類名（例: 鶏もも肉、豚こま切れ肉、大根、トマト、白菜、さば、鮭、りんご など）",
    "raw_name": "チラシに記載されている通りの正確な商品名（例: 青森などの国内産 りんご 1コ）",
    "price": 129,
    "unit": "単位や規格（例: 1個、100g、1パック、1本 など）",
    "valid_from": "YYYY-MM-DD",
    "valid_to": "YYYY-MM-DD",
    "date_evidence": "チラシに印刷されている実際の日付表記（例: 10/14限り、10/15限り、10/16〜10/18 など）",
    "is_today_only": trueまたはfalse,
    "note": "特売条件やチラシ記載の備考（例: 水曜限り！お一人様4点限り、よりどり3点99円 など）"
  }}
]
"""

    candidate_models = get_active_gemini_models(GEMINI_API_KEY)
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_img
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.0
        }
    }

    headers = {"Content-Type": "application/json"}

    for model_idx, current_model in enumerate(candidate_models):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={GEMINI_API_KEY}"
        print(f"  👉 [{model_idx + 1}/{len(candidate_models)}] モデル '{current_model}' で解析を試行中...", flush=True)

        # 最大2回まで試行（429時は15秒だけ待機、回復しなければ即スキップして全体を止めない）
        for retry_count in range(2):
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=40)
                if res.status_code == 200:
                    data = res.json()
                    text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                    deals = json.loads(text_content)
                    if isinstance(deals, list):
                        print(f"[OK] Gemini AI ({current_model}) が {store_name} のチラシから {len(deals)} 品の特売品を自律抽出しました！", flush=True)
                        return deals
                    return []
                elif res.status_code == 429:
                    if retry_count == 0:
                        wait_sec = 15
                        print(f"[WARN] APIレート制限 (HTTP 429)。{wait_sec}秒 待機して1度だけ再試行します...", flush=True)
                        time.sleep(wait_sec)
                        continue
                    else:
                        print(f"[WARN] API利用枠が一時的に満杯のため、この画像はスキップして次へ進みます", flush=True)
                        return []
                elif res.status_code == 503:
                    wait_sec = 8
                    print(f"[WARN] モデル '{current_model}' が混雑中 (HTTP 503)。{wait_sec}秒 待機して再試行します...")
                    time.sleep(wait_sec)
                    continue
                else:
                    print(f"[WARN] モデル '{current_model}' でエラー (HTTP {res.status_code}): {res.text[:150]}。代替モデルへ移行します...")
                    break
            except requests.exceptions.Timeout:
                wait_sec = 8
                print(f"[WARN] モデル '{current_model}' がタイムアウト。{wait_sec}秒 待機して再試行します...")
                time.sleep(wait_sec)
                continue
            except Exception as e:
                print(f"[ERROR] モデル '{current_model}' で例外エラー: {e}。代替モデルへ移行します...")
                break

    print(f"[-] {store_name}: 全モデル候補 ({len(candidate_models)}種) を試行しましたが抽出できませんでした")
    return []

if __name__ == "__main__":
    test_img = Path("flyers/beisia_day_1014.png")
    if test_img.exists():
        results = analyze_flyer_with_gemini(test_img, "ベイシア")
        print(json.dumps(results, ensure_ascii=False, indent=2))
