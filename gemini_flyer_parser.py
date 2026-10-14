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

_CACHED_ACTIVE_MODEL = None

def get_active_gemini_model(api_key: str) -> str:
    """Google APIに問い合わせて、現在利用可能な最新のGeminiモデルを自動検知"""
    global _CACHED_ACTIVE_MODEL
    if _CACHED_ACTIVE_MODEL:
        return _CACHED_ACTIVE_MODEL

    try:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        res = requests.get(list_url, timeout=10)
        if res.status_code == 200:
            models = res.json().get("models", [])
            # generateContent に対応したモデルを抽出
            supported = [
                m["name"].replace("models/", "")
                for m in models
                if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
            # 画像解析に強く混雑制限を受けにくい本格Flashモデルを優先（liteは除外）
            flash_models = [m for m in supported if "flash" in m.lower() and "lite" not in m.lower()]
            candidate_list = flash_models if flash_models else supported
            if candidate_list:
                # 'latest' が含まれる本格Flashモデルを最優先（例: gemini-1.5-flash-latest）
                latest_models = [m for m in candidate_list if "latest" in m.lower()]
                # バージョン順にソート
                sorted_models = sorted(candidate_list, reverse=True)
                chosen = latest_models[0] if latest_models else sorted_models[0]
                _CACHED_ACTIVE_MODEL = chosen
                print(f"[INFO] 🤖 Google公式APIから利用可能な最新本格モデルを動的検知・採用しました: {_CACHED_ACTIVE_MODEL}")
                return _CACHED_ACTIVE_MODEL
    except Exception as e:
        print(f"[WARN] モデル一覧の自動取得に失敗したため既定値を使用: {e}")

    _CACHED_ACTIVE_MODEL = "gemini-1.5-flash-latest"
    return _CACHED_ACTIVE_MODEL

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

    # 画像を文字鮮明度を保ったまま最適サイズ・JPEGに自動軽量化（3MB -> 300~500KB）
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            max_dimension = 1600
            if max(img.width, img.height) > max_dimension:
                scale = max_dimension / max(img.width, img.height)
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85, optimize=True)
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

このチラシ画像に実際に掲載されている【野菜】【きのこ】【果物】【精肉（豚・鶏・牛）】【鮮魚・水産】の日替わり特売品を正確に読み取り、JSON配列形式で抽出してください。

【厳格な遵守ルール】
1. 推測や架空の価格は絶対に含めず、画像に印刷されている数字のみを正確に読み取ること。
2. 価格（price）は「税抜（本体）価格」を整数値で出力してください。税込しか書かれていない場合は税込価格を整数で出力してください。
3. 日替わり枠（例: 10/14限り、10/15限り、10/16〜10/18など）の日付を正確に YYYY-MM-DD 形式に変換してください。
4. 惣菜、冷凍加工品、ピザ、お菓子などは除外し、新鮮な生鮮食品（野菜・肉・魚・きのこ・果物）を中心に抽出してください。

【出力フォーマット（JSON形式）】
[
  {{
    "ingredient": "食材の大分類名（例: 鶏もも肉、豚こま切れ肉、大根、トマト、白菜、さば、鮭、りんご など）",
    "raw_name": "チラシに記載されている通りの正確な商品名（例: 青森などの国内産 りんご 1コ）",
    "price": 129,
    "unit": "単位や規格（例: 1個、100g、1パック、1本 など）",
    "valid_from": "YYYY-MM-DD",
    "valid_to": "YYYY-MM-DD",
    "is_today_only": trueまたはfalse,
    "note": "特売条件やチラシ記載の備考（例: 水曜限り！お一人様4点限り、よりどり3点99円 など）"
  }}
]
"""

    active_model = get_active_gemini_model(GEMINI_API_KEY)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{active_model}:generateContent?key={GEMINI_API_KEY}"
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
            "temperature": 0.1
        }
    }

    headers = {"Content-Type": "application/json"}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=60)
            if res.status_code == 200:
                data = res.json()
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                deals = json.loads(text_content)
                if isinstance(deals, list):
                    print(f"[OK] Gemini AI が {store_name} のチラシから {len(deals)} 品の特売品を自律抽出しました！")
                    return deals
                return []
            elif res.status_code == 503:
                # 混雑エラーの場合は待機して再試行
                wait_sec = (attempt + 1) * 3
                print(f"[WARN] Gemini API が混雑中 (HTTP 503)。{wait_sec}秒後に再試行します... (試行 {attempt + 1}/{max_retries})")
                time.sleep(wait_sec)
                continue
            else:
                print(f"[ERROR] Gemini API エラー (HTTP {res.status_code}): {res.text}")
                return []
        except requests.exceptions.Timeout:
            wait_sec = (attempt + 1) * 3
            print(f"[WARN] Gemini API タイムアウト。{wait_sec}秒後に再試行します... (試行 {attempt + 1}/{max_retries})")
            time.sleep(wait_sec)
            continue
        except Exception as e:
            print(f"[ERROR] Gemini解析処理エラー: {e}")
            return []

    print(f"[-] {store_name}: 最大試行回数 ({max_retries}回) を超えたためスキップします")
    return []

if __name__ == "__main__":
    test_img = Path("flyers/beisia_day_1014.png")
    if test_img.exists():
        results = analyze_flyer_with_gemini(test_img, "ベイシア")
        print(json.dumps(results, ensure_ascii=False, indent=2))
