#!/bin/bash

merge_subtitles() {
    local base_name="$1"
    local segment_length="${2:-600}"
    
    if [ -z "$base_name" ]; then
        echo "使用方法: $0 <ベース名> [分割時間]"
        echo "例: $0 long_video 600"
        return 1
    fi
    
    echo "🔗 字幕ファイルを統合中: ${base_name}"
    
    local merged_file="output/${base_name}_merged_editable.srt"
    local counter=1
    
    > "$merged_file"  # ファイルを空にする
    
    for i in $(seq -f "%02g" 0 20); do  # part00からpart20まで確認
        local srt_file="output/${base_name}_part${i}_editable.srt"
        
        if [ ! -f "$srt_file" ]; then
            continue
        fi
        
        echo "📝 統合中: $srt_file"
        
        # 時間オフセット（秒）
        local time_offset=$((i * segment_length))
        
        # SRTファイルの内容を時間調整して追加
        python3 << PYTHON
import re
import sys

def add_seconds_to_timestamp(timestamp, offset_seconds):
    """SRTのタイムスタンプに秒を追加"""
    time_parts = timestamp.replace(',', ':').split(':')
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = int(time_parts[2])
    milliseconds = int(time_parts[3])
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + offset_seconds
    milliseconds_total = milliseconds
    
    new_hours = total_seconds // 3600
    new_minutes = (total_seconds % 3600) // 60
    new_seconds = total_seconds % 60
    
    return f"{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d},{milliseconds_total:03d}"

def process_srt_file(input_file, output_file, time_offset, start_counter):
    """SRTファイルを処理して統合"""
    counter = start_counter
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # SRTブロックに分割
    blocks = content.strip().split('\n\n')
    
    with open(output_file, 'a', encoding='utf-8') as f:
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # 番号を更新
                f.write(f"{counter}\n")
                
                # 時間行を処理
                time_line = lines[1]
                if ' --> ' in time_line:
                    start_time, end_time = time_line.split(' --> ')
                    new_start = add_seconds_to_timestamp(start_time.strip(), time_offset)
                    new_end = add_seconds_to_timestamp(end_time.strip(), time_offset)
                    f.write(f"{new_start} --> {new_end}\n")
                
                # テキスト行
                for text_line in lines[2:]:
                    f.write(f"{text_line}\n")
                
                f.write("\n")
                counter += 1
    
    return counter

# 実行
process_srt_file('$srt_file', '$merged_file', $time_offset, $counter)
PYTHON
        
        # 次の開始番号を取得
        counter=$(tail -n 20 "$merged_file" | grep -E '^[0-9]+$' | tail -1)
        counter=$((counter + 1))
    done
    
    echo "✅ 統合完了: $merged_file"
    echo "📊 総字幕数: $((counter - 1))"
}

# 実行
if [ $# -eq 0 ]; then
    echo "使用方法: $0 <ベース名> [分割時間]"
    echo "例: $0 long_video 600"
    exit 1
fi

merge_subtitles "$1" "$2"
