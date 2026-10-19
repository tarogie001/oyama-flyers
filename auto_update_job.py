"""
auto_update_job.py
朝8時09分にWindowsのバックグラウンドタスクとして自動実行される更新スクリプト
- チャットセッションをブロックせず、OSのバックグラウンドで静かに動作
- 当日の最新レポート生成、アプリ配信用JSON更新、Gitプッシュを実行
- API混雑（BUSY/429）時は無理な推測を行わず、安全に警告ログを記録
"""

import sys
import os
import datetime
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 作業ディレクトリをスクリプトのある場所に設定
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

LOG_FILE = BASE_DIR / "auto_job.log"
STATUS_FILE = BASE_DIR / "latest_run_status.txt"

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def run_command(cmd_list):
    res = subprocess.run(cmd_list, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.returncode, res.stdout, res.stderr

def main():
    log("==================================================")
    log("🚀 朝の自動更新バッチを開始します")
    
    today_str = datetime.date.today().isoformat()
    log(f"📅 対象基準日: {today_str}")

    # 1. Web上の新着チラシ掲載状況をチェック
    log("🔍 各スーパーの新着チラシ公開状況をチェック中...")
    python_exe = sys.executable
    ret_chk, out_chk, _ = run_command([python_exe, "check_online_flyers.py"])
    if ret_chk == 0:
        log("✅ チラシ公開状況の確認完了")
    else:
        log("⚠️ チラシ確認中に軽微な警告がありました（処理は継続します）")

    # 2. notifier.py を実行して当日のレポートおよび latest_deals.json を生成
    ret, stdout, stderr = run_command([python_exe, "notifier.py", today_str])
    
    if ret != 0:
        if "429" in stderr or "RESOURCE_EXHAUSTED" in stderr or "429" in stdout:
            err_msg = f"⚠️ Gemini APIが混雑（BUSY/429）しているため解析を安全にスキップしました。"
            log(err_msg)
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                f.write(f"{err_msg}\n{stderr}\n")
            return
        else:
            log(f"❌ notifier.py 実行エラー (code {ret}): {stderr}")
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                f.write(f"エラー発生: {stderr}\n")
            return

    log("✅ 最新レポートおよびアプリ用データの生成に成功しました")

    # 2. git status を確認し、変更があればコミット＆プッシュ
    ret, stdout, _ = run_command(["git", "status", "--porcelain"])
    modified_files = []
    for line in stdout.splitlines():
        if any(f in line for f in ["latest_deals.json", "deals.db", "today_report.txt"]):
            modified_files.append(line)

    if not modified_files:
        log("ℹ️ 更新対象の差分はありませんでした（すでに最新です）")
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] 更新差分なし（正常終了）\n")
        return

    log(f"📦 変更を検出しました: {len(modified_files)} 件のファイルをGitへ反映します")
    run_command(["git", "add", "latest_deals.json", "deals.db", "today_report.txt"])
    commit_msg = f"chore(auto): daily update for {today_str} [skip ci]"
    run_command(["git", "commit", "-m", commit_msg])
    
    ret, push_out, push_err = run_command(["git", "push", "origin", "main"])
    if ret == 0:
        log("🎉 GitHub Pagesへのプッシュ（デプロイ）が正常に完了しました！")
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] デプロイ成功: {today_str}\n")
    else:
        log(f"⚠️ Git push エラー: {push_err}")
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] Git push失敗: {push_err}\n")

if __name__ == "__main__":
    main()
