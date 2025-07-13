#作業メモ
#googletransのclient.pyの変数名変更：httpcore.SyncHTTPTransport -> httpcore.AsyncHTTPProxy

import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
import pytesseract
from PIL import ImageGrab, ImageOps
from pypinyin import lazy_pinyin, Style
from googletrans import Translator
from gtts import gTTS
import tkinter as tk
from tkinter import scrolledtext
import pyautogui
import time

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# ※ Tesseractのパス設定（必要な場合のみ）
tesseract_path = os.environ.get("TESSERACT_CMD_PATH")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
#再翻訳用のgoogletrans
translator = Translator() 

# 前回のオリジナルテキストと翻訳結果を保持するための変数
last_original_text = ""
last_translated_text = ""
last_pinyined_text = ""
last_retranslated_text = ""

region = (0, 100, 1920, 980)  # (left, top, right, bottom)

def capture_text(region):
    """
    指定された画面領域 (left, top, right, bottom) をキャプチャし、
    pytesseractを用いてテキストを抽出する（日本語を想定）。
    """
    screenshot = ImageGrab.grab(bbox=region)
    # グレースケール変換
    gray = ImageOps.grayscale(screenshot)
    # 二値化（閾値は環境や文字色に応じて調整してください、x<240は白文字を読む設定）
    bw = gray.point(lambda x: 0 if x < 240 else 255, '1')
    # OCRでテキスト抽出
    text = pytesseract.image_to_string(bw, lang='jpn', config = "--psm 6")
    return text

def translate_text(text):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"「」内の文章はOCRによるもので、文字が間違っている場合もあります。台湾での中国語に翻訳して、翻訳文のみを出力してください。「{text}」",
            )
        return response.text
    except Exception as e:
        return f"gemini翻訳エラー: {e}"

def pinyin_text(text):
    try:
        # ピンインを取得（tone3 は声調を数字で表示、tone ならアクセント記号）
        pinyin_list = lazy_pinyin(text, style=Style.TONE)
        # リストをスペース区切りの文字列に変換
        pinyin_text = " ".join(pinyin_list)
        return pinyin_text
    except Exception as e:
        return f"pinyinエラー: {e}"

def retranslate_text(text):
    try:
        result = translator.translate(text, src='zh-tw', dest='ja')
        return result.text 
    except Exception as e:
        return f"再翻訳エラー: {e}"       

def play_audio(text):
    """
    gTTSを使って、引数のテキスト（繁体字中国語）を音声化し再生する。
    """
    try:
        tts = gTTS(text, lang='zh-tw')
        filename = "output.mp3"
        tts.save(filename)
        # Windowsの場合、デフォルトのプレイヤーで再生
        os.system(f"start {filename}")
    except Exception as e:
        print(f"Audio playback error: {e}")

def update_translation():
    """
    指定領域をキャプチャし、OCRでテキスト抽出→翻訳を行い、
    GUIのテキストエリアにオリジナルテキストと翻訳結果を表示する。
    前回と同じOCR結果の場合は翻訳を行わず、前回の翻訳結果を再利用する。
    翻訳結果表示後に gTTS による音声再生を実行する。
    """
    global last_original_text, last_translated_text, last_pinyined_text, last_retranslated_text

    # キャプチャしてテキスト抽出
    original_text = capture_text(region)
    # 半角スペース、改行コードを除去
    original_text = original_text.replace(" ", "").replace("\n", "").replace("\r", "")
    
    if original_text.strip():
        if original_text != last_original_text:
            # OCR結果が変わっている場合のみ翻訳を実行
            translated = translate_text(original_text)
            pinyined = pinyin_text(translated)
            retranslated = retranslate_text(translated)
            last_original_text = original_text
            last_translated_text = translated
            last_pinyined_text = pinyined
            last_retranslated_text = retranslated
        else:
            # 前回と同じ場合は、前回の翻訳結果を使用
            translated = last_translated_text
    else:
        translated = "テキストが検出されませんでした。"

    # テキストエリアを更新（オリジナルテキストと翻訳結果を表示）
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, "=== Original Text ===\n" + original_text + "\n\n")
    text_area.insert(tk.END, "=== Translated Text ===\n" + translated + pinyined + "\n")
    text_area.insert(tk.END, "=== Retranslated Text ===\n" + retranslated + "\n")
    text_area.config(state=tk.DISABLED)

    # 翻訳結果のテキストを用いて音声再生を行う
    play_audio(translated)

def start_capture():
    """
    ボタン押下時に呼ばれる関数。
    OCR・翻訳・音声再生の一連の処理を実行する。
    """
    update_translation()

def set_capture_region():
    """
    マウスクリックで左上・右下座標を取得し、regionを設定する。
    """
    global region
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, "5秒以内にキャプチャしたいエリアの左上をクリックしてください...\n")
    text_area.config(state=tk.DISABLED)
    root.update()
    time.sleep(0.5)
    x1, y1 = pyautogui.position()
    for i in range(5, 0, -1):
        text_area.config(state=tk.NORMAL)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, f"{i}秒後に左上座標を取得します。マウスを移動してください。\n")
        text_area.config(state=tk.DISABLED)
        root.update()
        time.sleep(1)
    x1, y1 = pyautogui.position()

    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, "5秒以内に右下をクリックしてください...\n")
    text_area.config(state=tk.DISABLED)
    root.update()
    time.sleep(0.5)
    x2, y2 = pyautogui.position()
    for i in range(5, 0, -1):
        text_area.config(state=tk.NORMAL)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, f"{i}秒後に右下座標を取得します。マウスを移動してください。\n")
        text_area.config(state=tk.DISABLED)
        root.update()
        time.sleep(1)
    x2, y2 = pyautogui.position()

    region = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, f"新しいキャプチャエリア: {region}\n")
    text_area.config(state=tk.DISABLED)
    root.update()

interval_sec = 5  # 自動実行のインターバル（秒）
auto_mode = False  # 自動実行モードフラグ

def auto_update():
    if auto_mode:
        update_translation()
        root.after(interval_sec * 1000, auto_update)

def toggle_auto_mode():
    global auto_mode
    auto_mode = not auto_mode
    if auto_mode:
        area_button.config(state=tk.DISABLED)
        start_button.config(state=tk.DISABLED)
        auto_button.config(text="自動翻訳OFF")
        auto_update()
    else:
        area_button.config(state=tk.NORMAL)
        start_button.config(state=tk.NORMAL)
        auto_button.config(text="自動翻訳ON")

# GUIの構築
root = tk.Tk()
root.title("OCR・翻訳・音声再生")

# スクロール付きテキストエリア（結果表示用）
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20, font=("Arial", 14))
text_area.pack(padx=10, pady=10)
text_area.config(state=tk.DISABLED)

# 「開始キャプチャ」ボタンの配置
start_button = tk.Button(root, text="開始キャプチャ", command=start_capture, font=("Arial", 14))
start_button.pack(padx=10, pady=10)

# 「エリア設定」ボタンの追加
area_button = tk.Button(root, text="エリア設定", command=set_capture_region, font=("Arial", 14))
area_button.pack(padx=10, pady=5)

# 「自動翻訳ON/OFF」ボタンの追加
auto_button = tk.Button(root, text="自動翻訳ON", command=toggle_auto_mode, font=("Arial", 14))
auto_button.pack(padx=10, pady=5)

root.mainloop()