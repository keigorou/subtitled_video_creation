#!/bin/bash

echo "🎬 シンプル字幕ワークフロー"
echo ""

show_help() {
   echo "使用方法: ./workflow.sh [ステップ] [オプション]"
   echo ""
   echo "ステップ:"
   echo "  1. generate   - 動画からSRTファイルを作成"
   echo "  2. apply      - SRTから引数指定でスタイル付き動画作成"
   echo "  list          - 利用可能なファイルを表示"
   echo ""
   echo "apply のオプション:"
   echo "  --size NUM         フォントサイズ (デフォルト: 24)"
   echo "  --color COLOR      文字色 (white, red, blue, green, yellow)"
   echo "  --bold             太字にする"
   echo "  --italic           斜体にする"
   echo "  --outline NUM      アウトライン幅 (デフォルト: 2)"
   echo "  --position POS     位置 (bottom, top, center)"
   echo "  --margin NUM       マージン (デフォルト: 40)"
   echo "  --background COLOR 背景色 (black, white, gray, none)"
   echo "  --background-alpha NUM 背景透明度 (0.0-1.0, デフォルト: 0.8)"
   echo ""
   echo "例:"
   echo "  ./workflow.sh generate"
   echo "  ./workflow.sh apply --size 32 --color yellow --bold"
   echo "  ./workflow.sh apply --size 28 --color white --background black"
   echo "  ./workflow.sh apply --color white --background black --background-alpha 0.9"
}

mkdir -p videos output merged_videos

case "$1" in
   "generate"|"1")
       echo "📍 Step 1: 動画からSRTファイルを作成"
       
       # 動画ファイルがあるかチェック
       video_count=$(find videos -name "*.mp4" -o -name "*.avi" -o -name "*.mkv" -o -name "*.mov" 2>/dev/null | wc -l)
       if [ $video_count -eq 0 ]; then
           echo "❌ videos/ ディレクトリに動画ファイルがありません"
           echo "📁 動画ファイルを videos/ に配置してください"
           exit 1
       fi
       
       echo "🎬 発見された動画ファイル:"
       find videos -name "*.mp4" -o -name "*.avi" -o -name "*.mkv" -o -name "*.mov" 2>/dev/null | while read file; do
           size=$(du -h "$file" 2>/dev/null | cut -f1)
           echo "  - $file ($size)"
       done
       
       # SRT生成（シンプルモード）
       docker-compose -f docker-compose.yml up generate-subtitles
       
       echo ""
       echo "✅ Step 1 完了"
       echo ""
       echo "📁 生成されたSRTファイル:"
       find output -name "*.srt" -type f 2>/dev/null | while read file; do
           size=$(wc -l < "$file" 2>/dev/null)
           echo "  📝 $file ($size lines)"
       done
       echo ""
       echo "📝 次は以下のコマンドでスタイル付き動画を作成:"
       echo "   ./workflow.sh apply --size 32 --color yellow --bold"
       echo "   ./workflow.sh apply --color white --background black"
       ;;
   
   "apply"|"2")
       echo "📍 Step 2: SRTからスタイル付き動画を作成"
       
       # 引数を解析
       shift  # "apply" を削除
       
       # デフォルト値
       SIZE="24"
       COLOR="white"
       BOLD="false"
       ITALIC="false"
       OUTLINE="2"
       POSITION="bottom"
       MARGIN="40"
       BACKGROUND="none"
       BACKGROUND_ALPHA="0.8"
       
       # 引数を処理
       while [[ $# -gt 0 ]]; do
           case $1 in
               --size)
                   SIZE="$2"
                   shift 2
                   ;;
               --color)
                   COLOR="$2"
                   shift 2
                   ;;
               --bold)
                   BOLD="true"
                   shift
                   ;;
               --italic)
                   ITALIC="true"
                   shift
                   ;;
               --outline)
                   OUTLINE="$2"
                   shift 2
                   ;;
               --position)
                   POSITION="$2"
                   shift 2
                   ;;
               --margin)
                   MARGIN="$2"
                   shift 2
                   ;;
               --background)
                   BACKGROUND="$2"
                   shift 2
                   ;;
               --background-alpha)
                   BACKGROUND_ALPHA="$2"
                   shift 2
                   ;;
               *)
                   echo "❌ 不明なオプション: $1"
                   show_help
                   exit 1
                   ;;
           esac
       done
       
       # SRTファイルがあるかチェック
       srt_count=$(find output -name "*.srt" -type f 2>/dev/null | wc -l)
       if [ $srt_count -eq 0 ]; then
           echo "❌ SRTファイルが見つかりません"
           echo "📝 まず字幕を生成してください:"
           echo "   ./workflow.sh generate"
           exit 1
       fi
       
       # 設定を表示
       echo "🎨 スタイル設定:"
       echo "  📏 サイズ: $SIZE"
       echo "  🎨 色: $COLOR"
       echo "  💪 太字: $BOLD"
       echo "  📐 斜体: $ITALIC"
       echo "  🖼️ アウトライン: $OUTLINE"
       echo "  📍 位置: $POSITION"
       echo "  📏 マージン: $MARGIN"
       echo "  🎯 背景: $BACKGROUND"
       if [ "$BACKGROUND" != "none" ]; then
           echo "  👻 背景透明度: $BACKGROUND_ALPHA"
       fi
       echo ""
       
       # スタイル付き動画を作成
       python srt_to_video.py \
           --size "$SIZE" \
           --color "$COLOR" \
           --bold "$BOLD" \
           --italic "$ITALIC" \
           --outline "$OUTLINE" \
           --position "$POSITION" \
           --margin "$MARGIN" \
           --background "$BACKGROUND" \
           --background-alpha "$BACKGROUND_ALPHA"
       
       echo "✅ Step 2 完了"
       echo "🎉 merged_videos/ を確認してください"
       
       # 結果表示
       echo ""
       echo "📁 生成された字幕付き動画:"
       find merged_videos -name "*_styled.mp4" -type f 2>/dev/null | while read file; do
           size=$(du -h "$file" 2>/dev/null | cut -f1)
           echo "  🎬 $file ($size)"
       done
       ;;
   
   "list")
       echo "📁 利用可能なファイル:"
       echo ""
       echo "🎬 動画ファイル:"
       find videos -name "*.mp4" -o -name "*.avi" -o -name "*.mkv" -o -name "*.mov" 2>/dev/null | while read file; do
           size=$(du -h "$file" 2>/dev/null | cut -f1)
           echo "  - $file ($size)"
       done
       echo ""
       echo "📝 SRTファイル:"
       find output -name "*.srt" -type f 2>/dev/null | while read file; do
           lines=$(wc -l < "$file" 2>/dev/null)
           echo "  - $file ($lines lines)"
       done
       echo ""
       echo "🎬 字幕付き動画:"
       find merged_videos -name "*.mp4" -type f 2>/dev/null | while read file; do
           size=$(du -h "$file" 2>/dev/null | cut -f1)
           echo "  - $file ($size)"
       done
       ;;
   
   *)
       show_help
       ;;
esac
