# ゲーム画面をキャプチャして翻訳文と音声を出力することで外国語を勉強するためのアプリ
デフォルト設定は日本語->台湾の中国語
白文字で表示されている場合を認識することになっているので、ゲームに合わせて閾値設定を変更する。
GEMINIのAPIキーを環境変数に設定する。

# TESSERACTのインストールとパスの指定が必要。
.env
TESSERACT_CMD_PATH = "C:/Users/XXXXXX/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"