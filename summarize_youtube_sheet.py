import gspread
from oauth2client.service_account import ServiceAccountCredentials
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import re
import time

from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=api_key)

# ✅ Sheets用認証とクライアント
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_credential_path = os.getenv("GOOGLE_CREDENTIAL_PATH")
creds = ServiceAccountCredentials.from_json_keyfile_name(google_credential_path, scope)
sheet_client = gspread.authorize(creds)

# ✅ 対象シートの読み込み
sheet = sheet_client.open("youtubeURLリスト").sheet1
data = sheet.get_all_values()
print(f"取得したデータの行数: {len(data)}")
print(f"1行目: {data[0]}")

def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def fetch_transcript(video_id, retries=3, delay=2):
    """
    YouTubeの字幕を取得する関数。指定回数までリトライします。

    Parameters:
        video_id (str): YouTube動画のID
        retries (int): 最大リトライ回数（デフォルト：3回）
        delay (int): 各リトライ間の待機秒数（デフォルト：2秒）

    Returns:
        str or None: 字幕の全文テキスト（取得失敗時は None）
    """
    for attempt in range(1, retries + 1):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ja", "en"])
            return " ".join([entry["text"] for entry in transcript])
        except Exception as e:
            print(f"⚠️ 字幕取得失敗（{attempt}回目）: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                print("❌ 字幕取得を諦めます。")
                return None

def summarize_text(text):
    # 最大長を制限（約6000文字＝概ね最大8000トークン以下）
    
    max_length = 6000
    if len(text) > max_length:
        print(f"⚠️ 字幕が長すぎるためカットされました（{len(text)}文字 → {max_length}文字）")
        text = text[:max_length].rsplit(".", 1)[0]  # 最後の文の途中で切らない工夫

    prompt = (
    "次に示すのはYouTube動画の字幕の内容です。動画の最初から話されていると想定して、文頭が切れないよう自然な日本語で要約してください。\n\n"
    + text)
    
    response = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

for i in range(1, len(data)):  # 1行目はヘッダ
    url = data[i][2]
    print(f"\nProcessing row {i+1}: {url}")

    if len(data[i]) > 3 and data[i][3].strip():
        print("🔄 スキップ（すでにD列に要約あり）")
        continue

    video_id = extract_video_id(url)
    if not video_id:
        print("⚠️ URLエラー")
        sheet.update_cell(i+1, 4, "⚠️ URLエラー")
        continue

    transcript = fetch_transcript(video_id)
    if not transcript:
        print("⚠️ 字幕なし（transcriptがNone）")
        sheet.update_cell(i+1, 4, "⚠️ 字幕なし")
        continue

    try:
        summary = summarize_text(transcript)

        # ✅ 段落風改行（2つ）→ 通常の改行（1つ）
        summary = summary.replace("\r\n", "\n").replace("\r", "\n")  # OS依存の改行を統一
        summary = summary.replace("\n\n", "\n")  # 段落改行を1行の改行に変換

        print("✅ 要約取得成功！書き込み中...")
        sheet.update_cell(i+1, 4, summary)
    except Exception as e:
        print(f"❌ GPT要約エラー: {e}")
        sheet.update_cell(i+1, 4, f"❌ GPTエラー: {str(e)}")

    time.sleep(3)
