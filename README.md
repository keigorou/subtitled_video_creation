docker-compose -f docker-compose.yml up -d
docker exec audio-extractor python extract_audio.py


# 1. 動画からマーカー付き字幕を生成
docker-compose up video-to-text-markers

# 2. HTMLマーカー字幕を動画に合成
docker-compose up add-html-subtitles

# 3. ASSマーカー字幕を動画に合成
docker-compose up add-ass-subtitles

# 基本的なカスタム
docker-compose run --rm generate-subtitles python video_to_text_with_custom_styles.py --color red --size 32 --bold

# YouTube風カスタム
docker-compose run --rm generate-subtitles python video_to_text_with_custom_styles.py --font "Arial Black" --size 36 --color yellow --outline-width 4 --bold

# 映画風カスタム
docker-compose run --rm generate-subtitles python video_to_text_with_custom_styles.py --font "Times New Roman" --size 28 --italic --color white

# 16進数カラー使用
docker-compose run --rm generate-subtitles python video_to_text_with_custom_styles.py --color "#FF6600" --size 28 --position top

# 全自動パイプライン
docker-compose run --rm full-pipeline python full_pipeline.py --color blue --size 30 --bold

##############
# YouTube風全自動
docker-compose up full-pipeline-youtube

# ゲーム実況風全自動
docker-compose up full-pipeline-gaming

# 映画風全自動
docker-compose up full-pipeline-cinema

# カスタム引数で実行
docker-compose run --rm full-pipeline python full_pipeline.py --font "Arial Black" --size 32 --color red --bold


=============
字幕作成
docker-compose -f docker-compose.yml run --rm generate-subtitles python  video_to_text_with_custom_styles.py  --format srt --size 48
======================================================
#srtのみのシンプルな方法
動画からテキスト抽出
./workflow.sh generate

#テキストから動画に字幕をつける
# 基本的な使用
./workflow.sh apply --size 32 --color yellow --bold

# 詳細なカスタマイズ
./workflow.sh apply --size 28 --color red --bold --italic --outline 3 --margin 50

# 上部配置の字幕
./workflow.sh apply --size 24 --color white --position top --margin 60

=================================
マーカー
¥¥¥large-blue¥¥¥こんにちは！¥¥¥

# 1. 字幕生成
./marker_workflow.sh generate

# 2. 生成されたSRTファイルを編集してマーカーを追加
./marker_workflow.sh edit

# 3. マーカーを処理（新しいprocess_markers.pyを使用）
./marker_workflow.sh process

# 4. 動画に合成
./marker_workflow.sh apply