"""
run_daily.py
小山市周辺15店舗のチラシ収集、高解像度ブロック分割、提案レポート＆JSON出力を一括実行するスクリプト
（Windows/Linux/GitHub Actions共通で動作）
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_step(step_name: str, script_name: str):
    print(f"\n=======================================================")
    print(f"▶ {step_name} ({script_name}) を開始します...")
    print(f"=======================================================")
    script_path = BASE_DIR / script_name
    result = subprocess.run([sys.executable, str(script_path)], cwd=str(BASE_DIR))
    if result.returncode != 0:
        print(f"⚠️ {script_name} でエラーが発生しました (終了コード: {result.returncode})")
    else:
        print(f"✅ {step_name} が正常に完了しました。")

def main():
    print("======================================================")
    print(" 小山市周辺スーパー15店舗 チラシ自動収集＆提案パイプライン")
    print("======================================================")
    
    # 1. チラシ・特売情報の自動収集
    run_step("1. チラシ・特売情報の自動収集", "flyer_crawler.py")
    
    # 2. チラシ画像の高解像度ブロック分割
    run_step("2. チラシ高解像度ブロック分割処理", "flyer_image_processor.py")
    
    # 3. 買い出し提案レポート生成＆アプリ用JSON出力
    run_step("3. 提案レポート生成＆JSON出力", "notifier.py")
    
    print("\n🎉 すべての自動更新プロセスが完了しました！")

if __name__ == "__main__":
    main()
