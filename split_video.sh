#!/bin/bash

split_video() {
    local input_video="$1"
    local segment_length="${2:-600}"  # デフォルト10分
    
    if [ ! -f "$input_video" ]; then
        echo "❌ ファイルが見つかりません: $input_video"
        return 1
    fi
    
    local basename=$(basename "$input_video" .mp4)
    
    # 分割専用のフォルダ構造を作成
    mkdir -p split/videos
    mkdir -p split/output
    mkdir -p split/merged_videos
    mkdir -p split/marker_output
    
    echo "🔄 動画分割開始"
    echo "📹 入力ファイル: $input_video"
    echo "⏱️  分割時間: ${segment_length}秒 ($(($segment_length/60))分)"
    echo "📁 出力先: split/videos/"
    
    # 動画の総時間を取得
    duration=$(ffprobe -v quiet -show_entries format=duration -of csv="p=0" "$input_video" 2>/dev/null)
    
    if [ -z "$duration" ]; then
        echo "❌ 動画の長さを取得できませんでした"
        return 1
    fi
    
    # 分割数を計算
    segments=$(awk "BEGIN {print int(($duration + $segment_length - 1) / $segment_length)}")
    
    echo "📊 動画情報:"
    echo "  総時間: ${duration}秒 ($(printf "%.1f" $(echo "$duration/60" | bc -l))分)"
    echo "  分割数: ${segments}個"
    
    echo ""
    echo "🎬 分割処理開始..."
    
    for i in $(seq 0 $((segments-1))); do
        start_time=$((i * segment_length))
        output_file="split/videos/${basename}_part$(printf "%02d" $i).mp4"
        
        echo "  📹 Part $((i+1))/$segments: ${basename}_part$(printf "%02d" $i).mp4"
        echo "     開始時間: ${start_time}秒 ($(($start_time/60))分$(($start_time%60))秒)"
        
        ffmpeg -i "$input_video" \
               -ss $start_time \
               -t $segment_length \
               -c copy \
               -avoid_negative_ts make_zero \
               "$output_file" \
               -y -loglevel error
        
        if [ $? -eq 0 ]; then
            size=$(du -h "$output_file" | cut -f1)
            echo "     ✅ 完了: $size"
        else
            echo "     ❌ 失敗"
            return 1
        fi
    done
    
    echo ""
    echo "🎉 分割完了!"
    echo "📁 分割されたファイル:"
    ls -lh split/videos/${basename}_part*.mp4 | while read line; do
        echo "  $line"
    done
    
    echo ""
    echo "📁 作成されたフォルダ構造:"
    echo "  split/"
    echo "  ├── videos/         # 分割された動画ファイル"
    echo "  ├── output/         # 字幕ファイル（SRT/ASS）"
    echo "  ├── marker_output/  # マーカー処理済み字幕"
    echo "  └── merged_videos/  # 字幕付き動画"
    
    echo ""
    echo "📋 次のステップ:"
    echo "  ./split_workflow.sh generate  # 分割動画の字幕生成"
}

# ヘルプ表示
show_help() {
    echo "📹 動画分割ツール（分割専用フォルダ対応）"
    echo ""
    echo "使用方法:"
    echo "  $0 <動画ファイル> [分割時間(秒)]"
    echo ""
    echo "例:"
    echo "  $0 videos/long_video.mp4          # 10分ずつ分割"
    echo "  $0 videos/long_video.mp4 300      # 5分ずつ分割"
    echo "  $0 videos/long_video.mp4 180      # 3分ずつ分割"
    echo ""
    echo "出力先:"
    echo "  split/videos/       # 分割された動画"
    echo "  split/output/       # 字幕ファイル"
    echo "  split/merged_videos/ # 字幕付き動画"
}

# 引数チェック
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# 実行
split_video "$1" "$2"
