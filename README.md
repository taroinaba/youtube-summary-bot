# 🎥 YouTube 字幕要約ボット

YouTube の字幕を自動取得し、OpenAI GPT を使って日本語で要約し、Googleスプレッドシートに保存する Python ボットです。

---

## 🚀 機能概要

- YouTube URL をスプレッドシートで管理
- 字幕を自動で取得（日本語/英語対応）
- OpenAI GPT-4.1-nano による自然な日本語要約
- スプレッドシートに直接出力

---

## 🛠️ 使用技術

- Python 3.9+
- gspread / oauth2client
- youtube-transcript-api
- OpenAI API
- Google Sheets API + Drive API

---

## 🧪 実行手順

### ① 必要ライブラリのインストール

```bash
pip install -r requirements.txt
