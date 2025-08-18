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

# 3. マーカーを処理（process_markers.pyを使用）
./marker_workflow.sh process

# 4. 動画に合成
./marker_workflow.sh apply --size 32 --color yellow --bold