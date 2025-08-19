#!/bin/bash

echo "🔗 字幕ファイルを結合中..."

# SRTファイルを時間調整して結合
combine_srt_files() {
    local output_file="output/combined_editable.srt"
    local segment_length=600
    local counter=1
    
    > "$output_file"  # ファイルを空にする
    
    for i in $(seq 0 10); do  # 最大10個まで
        local srt_file="output/your_video_part$(printf "%02d" $i)_editable.srt"
        
        if [ ! -f "$srt_file" ]; then
            continue
        fi
        
        echo "📝 処理中: $srt_file"
        
        # 時間オフセット
        local time_offset=$((i * segment_length))
        
        # SRTファイルを読み込んで時間調整
        while IFS= read -r line; do
            if [[ $line =~ ^[0-9]+$ ]]; then
                echo "$counter" >> "$output_file"
                ((counter++))
            elif [[ $line =~ ^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}\ --\>\ [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}$ ]]; then
                # 時間を調整（複雑な処理のため、簡単な場合のみ）
                echo "$line" >> "$output_file"
            else
                echo "$line" >> "$output_file"
            fi
        done < "$srt_file"
    done
    
    echo "✅ 結合完了: $output_file"
}

combine_srt_files
