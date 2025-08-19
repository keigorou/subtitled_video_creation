=============
字幕作成
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
./marker_workflow.sh process --size 32 --color yellow --bold

# 4. 動画に合成
./marker_workflow.sh apply --size 32 --color yellow --bold

3,4のスタイル指定は同じにする

=========================================================================
オプション     型     デフォルト 説明              例
--size       数値    24       フォントサイズ    --size 32
--color      文字列  white    文字色           --color yellow
--bold       -      false    太字にする        --bold
--italic     -      false    斜体にする        --italic
--outline    数値    2        アウトライン幅    --outline 3
--position   文字列  bottom   字幕位置          --position top
--margin     数値    40       マージン          --margin 60
--background 文字列  none     背景色            --background black
--background -      alpha    小数 0.8背景透明度 --background-alpha 0.9

文字色・背景色: white, red, blue, green, yellow, black, cyan, magenta, gray

使用可能な位置 top center bottom
=========================================================================
使用可能なマーカー

サイズ: large, small
色: red, blue, green, yellow, white, black
スタイル: bold, italic

🔗 組み合わせ例:"
    echo "    size48-red-bold"
    echo "    large-blue"
    echo "    size32-green-italic"
    echo "    small-yellow"

=========================================================================
#生成ファイル削除
rm marker_output/* merged_videos/* output/*

#docker 不要なimage 削除
docker system prune -a

=========================================================================
#動画を分割
# 基本的な使用（10分ずつ分割）
./split_video.sh videos/your_video.mp4

# 5分ずつ分割
./split_video.sh videos/your_video.mp4 300

# 3分ずつ分割
./split_video.sh videos/your_video.mp4 180

#分割した動画からsrt作成
./split_workflow.sh generate --model small

#srtを統合
 ./split_workflow.sh combine --segment-length 300   

 あとは動画に合成