FROM python:3.9

# システムパッケージをインストール
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
    fonts-noto-cjk \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Pythonライブラリをインストール
RUN pip install --no-cache-dir \
    openai-whisper \
    torch \
    torchaudio \
    chardet \
    jaconv \
    mojimoji \
    neologdn
# RUN pip install --no-cache-dir \
#     openai-whisper \
#     torch \
#     torchaudio \
#     chardet

# 作業ディレクトリを設定
WORKDIR /app

# スクリプトをコピー
COPY video_to_text_with_custom_styles.py .
COPY apply_subtitles.py .
COPY full_pipeline.py .

# デフォルト実行
# CMD ["python", "full_pipeline.py"]