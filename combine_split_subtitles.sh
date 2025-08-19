#!/bin/bash

combine_split_subtitles() {
    local base_name="$1"
    local segment_length="${2:-600}"
    
    if [ -z "$base_name" ]; then
        echo "❌ ベース名を指定してください"
        echo "使用方法: $0 <ベース名> [分割時間(秒)]"
        echo "例: $0 long_video 300"
        return 1
    fi
    
    echo "🔗 分割字幕ファイルを統合中"
    echo "📝 ベース名: $base_name"
    echo "⏱️  分割時間: ${segment_length}秒"
    
    # 出力先ディレクトリを確認
    mkdir -p output
    
    # 統合ファイル名
    local merged_editable="output/${base_name}_merged_editable.srt"
    
    echo "📁 出力先:"
    echo "  📝 編集可能SRT: $merged_editable"
    
    # 分割SRTファイルを確認
    local split_files=($(find split/output -name "${base_name}_part*_editable.srt" 2>/dev/null | sort))
    
    if [ ${#split_files[@]} -eq 0 ]; then
        echo "❌ 分割SRTファイルが見つかりません: split/output/${base_name}_part*_editable.srt"
        echo "📝 まず ./split_workflow.sh generate を実行してください"
        return 1
    fi
    
    echo ""
    echo "🔍 統合対象ファイル:"
    for file in "${split_files[@]}"; do
        lines=$(wc -l < "$file" 2>/dev/null)
        echo "  - $file ($lines lines)"
    done
    
    echo ""
    echo "⚙️  統合処理開始..."
    
    # Python統合スクリプトを実行（修正版）
    python3 << PYTHON
import re
import os
from pathlib import Path

def srt_time_to_seconds(time_str):
    """SRT時間をミリ秒に変換"""
    time_part, ms_part = time_str.split(',')
    h, m, s = map(int, time_part.split(':'))
    ms = int(ms_part)
    return (h * 3600 + m * 60 + s) * 1000 + ms

def seconds_to_srt_time(total_ms):
    """ミリ秒をSRT時間に変換"""
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def add_time_offset(time_str, offset_ms):
    """時間にオフセットを追加"""
    original_ms = srt_time_to_seconds(time_str)
    new_ms = original_ms + offset_ms
    return seconds_to_srt_time(new_ms)

def combine_srt_files(input_files, output_file, segment_length_sec):
    """複数のSRTファイルを統合"""
    
    combined_blocks = []
    subtitle_counter = 1
    
    for part_index, input_file in enumerate(input_files):
        if not os.path.exists(input_file):
            continue
            
        print(f"  📝 処理中: {os.path.basename(input_file)}")
        
        # 時間オフセット（ミリ秒）
        time_offset_ms = part_index * segment_length_sec * 1000
        
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            continue
        
        # SRTブロックに分割
        blocks = content.split('\\n\\n')
        
        for block in blocks:
            lines = block.strip().split('\\n')
            if len(lines) >= 3:
                # 番号行をスキップして新しい番号を割り当て
                time_line = lines[1]
                text_lines = lines[2:]
                
                if ' --> ' in time_line:
                    start_time, end_time = time_line.split(' --> ')
                    
                    # 時間オフセットを追加
                    new_start = add_time_offset(start_time.strip(), time_offset_ms)
                    new_end = add_time_offset(end_time.strip(), time_offset_ms)
                    
                    # 新しいブロックを作成
                    new_block = f"{subtitle_counter}\\n{new_start} --> {new_end}\\n" + '\\n'.join(text_lines)
                    combined_blocks.append(new_block)
                    subtitle_counter += 1
    
    # 統合ファイルを書き出し
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\\n\\n'.join(combined_blocks))
        if combined_blocks:  # 空でない場合のみ最後に改行
            f.write('\\n')
    
    return len(combined_blocks)

# ファイルリストを作成
input_files = [
$(printf '    "%s",\n' "${split_files[@]}")
]

# 末尾のカンマを削除
input_files = [f.strip(',') for f in input_files if f.strip(',')]

segment_length = ${segment_length}
output_file = "${merged_editable}"

subtitle_count = combine_srt_files(input_files, output_file, segment_length)
print(f"✅ 統合完了: {subtitle_count}個の字幕ブロック")

PYTHON
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 統合成功!"
        
        # ファイルサイズと行数を表示
        if [ -f "$merged_editable" ]; then
            lines=$(wc -l < "$merged_editable")
            size=$(du -h "$merged_editable" | cut -f1)
            echo "📊 統合結果:"
            echo "  📝 $merged_editable"
            echo "  📏 行数: $lines"
            echo "  📦 サイズ: $size"
        fi
        
        echo ""
        echo "📋 次のステップ:"
        echo "  1. nano $merged_editable  # 必要に応じて編集"
        echo "  2. ./marker_workflow.sh process --size 32 --color yellow --bold"
        echo "  3. ./marker_workflow.sh apply --size 32 --color yellow --bold"
        
    else
        echo "❌ 統合に失敗しました"
        return 1
    fi
}

# ヘルプ表示
show_help() {
    echo "🔗 分割SRT統合ツール"
    echo ""
    echo "使用方法:"
    echo "  $0 <ベース名> [分割時間(秒)]"
    echo ""
    echo "例:"
    echo "  $0 吉田あやの本音トークが炸裂 300     # 5分ずつ分割された場合"
    echo "  $0 講義動画 600                    # 10分ずつ分割された場合"
    echo ""
    echo "入力元: split/output/<ベース名>_part*_editable.srt"
    echo "出力先: output/<ベース名>_merged_editable.srt"
}

# 引数チェック
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# 実行
combine_split_subtitles "$1" "$2"
