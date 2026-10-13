# 🛒 小山市スーパー・薬局 特売お得買い出し支援ツール

小山市周辺のスーパー（13店舗）およびドラッグストア（2店舗・計15店舗）のチラシ特売情報を分析し、**1週間全体のスケジュールを見渡して「今日買うべき食材」と「後日安くなるので待つべき食材」**を毎日提案してくれる週間仕入れ最適化ツールです。

---

## 📁 ファイル構成

| ファイル名                                                                                                               | 役割                                                 |
| :------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------- |
| `run_daily.bat`                                                                                                     | **毎朝のワンクリック自動実行**。チラシ収集からレポート生成まで一括実行              |
| [weekly_planner.py](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/weekly_planner.py) | **週間仕入れ最適化エンジン**。1週間の最安値から「今日買うもの」「待つもの」「週間ルート」を判定 |
| [flyer_crawler.py](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/flyer_crawler.py)   | **自動リサーチクローラー**。小山市15店舗のチラシ掲載ページを自動巡回              |
| [ingredients.json](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/ingredients.json)   | 監視対象の食材リスト（野菜、肉、魚、調味料などカテゴリ別管理）                    |
| [stores.json](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/stores.json)             | 小山市周辺の確定15店舗リスト（各店舗のチラシ専用URL完備）                    |
| [deal_analyzer.py](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/deal_analyzer.py)   | 特売品データ管理・食材自動照合・データベース連携                           |
| [notifier.py](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/notifier.py)             | スマホ（LINEやメール）へレポートを送信し、ファイル保存するスクリプト               |
| [flyer_parser.py](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/flyer_parser.py)     | チラシ画像（AI解析）やテキスト貼り付けから特売品を取り込むスクリプト                |
| [config.json](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/config.json)             | LINE通知やメール通知の設定ファイル                                |
| [today_report.txt](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/today_report.txt)   | 自動生成された最新の買い出しおすすめレポート                             |
| `flyers/`                                                                                                           | チラシ画像を保存するフォルダ                                     |

---

## 🚀 日常の使い方

### 1. チラシ特売品を登録する
コマンド画面（PowerShellなど）で以下を実行します。
```powershell
python flyer_parser.py
```
メニューが表示されます。
- **「1」を選択**: チラシを見ながらメモ感覚で貼り付け登録ができます。
  ```text
  ヨークベニマル キャベツ 128円 1玉
  カワチ 納豆 58円 3パック
  ジャパンミート 豚バラ 128円 100g
  ```
  ※店舗名や単位は自動判定されます。

- **チラシ画像を自動読み取りする場合**:
  `flyers/` フォルダにチラシ画像（JPGまたはPNG）を保存し、`python flyer_parser.py` からAI自動解析を実行します。

---

### 2. 本日のおすすめレポートを確認・スマホに送る
```powershell
python notifier.py
```
- 最新のおすすめレポートが画面に表示され、[today_report.txt](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/today_report.txt) に保存されます。
- LINEやメールの設定をしている場合は、スマホへ直接プッシュ通知されます。

---

## 🛠️ 食材の追加・修正方法

食材を増やしたい場合や、チラシの表記ゆれを追加したい場合は、[ingredients.json](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/ingredients.json) を開いて直接追記・編集できます。

```json
{
  "野菜": [
    {
      "name": "トマト",
      "keywords": ["トマト", "とまと", "ミニトマト"]
    }
  ]
}
```

---

## 🏬 対象店舗一覧（14チェーン）

小山市周辺の以下の店舗が登録されています。店舗の追加や支店の変更は [stores.json](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/stores.json) で自由に行えます。

1. ヨークベニマル
2. ベイシア
3. とりせん
4. たいらや
5. フードオアシス オータニ
6. マルエツ
7. ベルク
8. かましん
9. ヤオハン
10. ジョイフーズ
11. トライアル
12. ジャパンミート
13. カワチ薬品
14. スギ薬局

---

## 📲 スマホ通知（LINE / メール）の設定

[config.json](file:///h:/%E3%83%9E%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%96/Daili-life/config.json) をメモ帳などで開いて設定します。

### ■ LINEで受け取る場合
1. LINE Developers で無料の「Messaging API（公式アカウント）」を作成します。
2. `method` を `"line"` に変更し、チャネルアクセストークンとユーザーIDを記入します。
```json
"method": "line",
"line": {
  "channel_access_token": "取得したトークン",
  "user_id": "あなたのユーザーID"
}
```

### ■ メールで受け取る場合
1. `method` を `"email"` に変更し、Gmail等の送信元アドレスとアプリパスワード、届先のスマホアドレスを入力します。
```json
"method": "email",
"email": {
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "sender_email": "your_email@gmail.com",
  "sender_password": "Googleアプリパスワード",
  "recipient_email": "your_phone@docomo.ne.jp"
}
```
