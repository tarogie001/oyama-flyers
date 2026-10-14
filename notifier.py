"""
notifier.py
生成された買い出しおすすめレポートを、LINE・メール・ファイルへ通知・送信するスクリプト
"""

import sys
import json
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from pathlib import Path
from weekly_planner import WeeklyPlanner

# Windows環境で文字化けを防ぐ設定
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
REPORT_OUTPUT_FILE = BASE_DIR / "today_report.txt"


class Notifier:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if not CONFIG_FILE.exists():
            return {}
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 設定ファイルの読み込みに失敗しました: {e}")
            return {}

    def save_to_file(self, message: str) -> bool:
        """最新のレポートをテキストファイルに書き出す"""
        try:
            with open(REPORT_OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(message)
            print(f"📄 レポートをファイルに保存しました: {REPORT_OUTPUT_FILE.name}")
            return True
        except Exception as e:
            print(f"❌ ファイル保存エラー: {e}")
            return False

    def send_line(self, message: str) -> bool:
        """LINE公式アカウント (Messaging API) からプッシュ通知を送信"""
        line_cfg = self.config.get("notification", {}).get("line", {})
        token = line_cfg.get("channel_access_token", "").strip()
        user_id = line_cfg.get("user_id", "").strip()

        if not token or "ここに" in token or not user_id or "ここに" in user_id:
            print("⚠️ LINE通知の設定が未入力です (config.json を設定してください)")
            return False

        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        data = {
            "to": user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req) as res:
                if res.status == 200:
                    print("✅ LINE通知を正常に送信しました！")
                    return True
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            print(f"❌ LINE送信失敗 (HTTP {e.code}): {error_body}")
        except Exception as e:
            print(f"❌ LINE送信エラー: {e}")
        return False

    def send_email(self, message: str) -> bool:
        """メール (SMTP) でレポートを送信"""
        mail_cfg = self.config.get("notification", {}).get("email", {})
        smtp_server = mail_cfg.get("smtp_server", "smtp.gmail.com")
        smtp_port = mail_cfg.get("smtp_port", 587)
        sender = mail_cfg.get("sender_email", "").strip()
        password = mail_cfg.get("sender_password", "").strip()
        recipient = mail_cfg.get("recipient_email", "").strip()

        if not sender or "@" not in sender or not recipient or "@" not in recipient:
            print("⚠️ メール通知の設定が未入力です (config.json を設定してください)")
            return False

        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = "🛒【本日の買い出しおすすめ】特売お知らせ"
        msg["From"] = sender
        msg["To"] = recipient

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            server.quit()
            print(f"✅ メールを送信しました！ ({recipient})")
            return True
        except Exception as e:
            print(f"❌ メール送信エラー: {e}")
            return False

    def notify(self, target_date: str = None):
        """設定に基づいて通知を実行"""
        planner = WeeklyPlanner()
        report = planner.generate_optimized_report(target_date)

        # 常に最新のレポートをファイルに保存
        self.save_to_file(report)
        planner.export_json_data(target_date)

        method = self.config.get("notification", {}).get("method", "file").lower()
        if method == "line":
            self.send_line(report)
        elif method == "email":
            self.send_email(report)
        elif method == "both":
            self.send_line(report)
            self.send_email(report)
        else:
            print("💡 現在の通知モードは [file] です。ファイル保存のみ実行しました。")


if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    notifier = Notifier()
    notifier.notify(target_date)

