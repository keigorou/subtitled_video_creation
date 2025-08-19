#!/bin/bash

echo "🎬 分割動画用字幕ワークフロー"
echo ""

show_help() {
    echo "使用方法: ./split_workflow.sh [ステップ] [オプション]"
    echo ""
    echo "⚠️  注意：このスクリプトは split/videos/ 内の分割動画を処理します"
    echo ""
    echo "ステップ:"
    echo "  1. generate   - 分割動画から字幕を生成"
    echo "  6. combine    - 分割SRTをoutput/に統合"
    echo "  list          - 利用可能なファイルを表示"
    echo ""
    echo "generate のオプション:"
    echo "  --model MODEL      Whisperモデル (tiny, base, small, medium)"
    echo ""
    echo "例:"
    echo "  ./split_workflow.sh generate --model medium"
    echo "  ./split_workflow.sh combine --segment-length 300"
}

case "$1" in
    "generate"|"1")
        echo "📍 Step 1: 分割動画から字幕を生成"
        
        # 分割動画があるかチェック
        video_count=$(find split/videos -name "*.mp4" 2>/dev/null | wc -l)
        if [ $video_count -eq 0 ]; then
            echo "❌ split/videos/ に動画ファイルがありません"
            echo "📝 まず ./split_video.sh で動画を分割してください"
            exit 1
        fi
        
        echo "🎬 発見された分割動画: ${video_count}個"
        
        # モデル引数を解析
        shift
        MODEL="tiny"  # デフォルト値
        while [[ $# -gt 0 ]]; do
            case $1 in
                --model)
                    MODEL="$2"
                    echo "🤖 使用モデル: $MODEL"
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done
        
        # 出力ディレクトリを作成
        mkdir -p split/output
        mkdir -p split/marker_output
        
        echo ""
        echo "🔄 分割動画用字幕生成を実行中..."
        echo "📋 実行コマンド: python video_to_text_with_custom_styles.py --model $MODEL --input-dir /input_videos --output-dir /output"
        
        # 手動テストと同じ形式で実行
        docker-compose run --rm split-generate-subtitles \
            python video_to_text_with_custom_styles.py \
            --model $MODEL \
            --input-dir /input_videos \
            --output-dir /output
        
        echo ""
        echo "✅ Step 1 完了"
        echo ""
        echo "📁 生成されたファイル:"
        find split/output -name "*_editable.srt" -type f 2>/dev/null | while read file; do
            size=$(wc -l < "$file" 2>/dev/null)
            echo "  📝 $file ($size lines)"
        done
        
        # 生成されたファイル数をカウント
        generated_count=$(find split/output -name "*_editable.srt" -type f 2>/dev/null | wc -l)
        echo ""
        echo "📊 結果: ${generated_count}/${video_count} 個のファイルを生成"
        
        if [ $generated_count -eq 0 ]; then
            echo ""
            echo "🔍 デバッグ情報:"
            echo "📁 split/output/ の内容:"
            ls -la split/output/ 2>/dev/null || echo "  ディレクトリが空です"
            echo ""
            echo "🐳 最新のDockerログ:"
            docker-compose logs --tail 50 split-generate-subtitles
        fi
        
        echo ""
        echo "📝 次のステップ:"
        echo "   ./split_workflow.sh combine --segment-length 300"
        ;;
    
    "combine"|"6")
        echo "📍 Step 6: 分割SRTファイルを統合してoutput/に保存"
        
        # 分割時間を引数から取得（デフォルト300秒）
        segment_length=300
        shift
        while [[ $# -gt 0 ]]; do
            case $1 in
                --segment-length)
                    segment_length="$2"
                    echo "⏱️  指定された分割時間: ${segment_length}秒"
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done
        
        # 分割SRTファイルを確認
        srt_count=$(find split/output -name "*_part*_editable.srt" -type f 2>/dev/null | wc -l)
        
        if [ $srt_count -eq 0 ]; then
            echo "❌ 分割SRTファイルが見つかりません"
            echo "📝 まず ./split_workflow.sh generate を実行してください"
            echo ""
            echo "📁 split/output/ の内容:"
            ls -la split/output/ 2>/dev/null || echo "  ディレクトリが空です"
            exit 1
        fi
        
        echo "📊 発見された分割SRTファイル: ${srt_count}個"
        
        # ベース名を自動検出
        first_srt=$(find split/output -name "*_part00_editable.srt" -type f 2>/dev/null | head -1)
        base_name=$(basename "$first_srt" | sed 's/_part00_editable\.srt$//')
        
        echo "🔍 自動検出されたベース名: $base_name"
        echo "⏱️  分割時間: ${segment_length}秒"
        
        # 統合スクリプトを実行
        ./combine_split_subtitles.sh "$base_name" "$segment_length"
        
        echo ""
        echo "✅ Step 6 完了"
        echo "📝 通常のワークフローで続行可能:"
        echo "   nano output/${base_name}_merged_editable.srt"
        echo "   ./marker_workflow.sh process --size 32 --color yellow --bold"
        echo "   ./marker_workflow.sh apply --size 32 --color yellow --bold"
        ;;
    
    "list")
        echo "📁 分割動画用ファイル一覧:"
        echo ""
        echo "🎬 分割された動画:"
        video_count=$(find split/videos -name "*.mp4" -type f 2>/dev/null | wc -l)
        if [ $video_count -gt 0 ]; then
            find split/videos -name "*.mp4" -type f 2>/dev/null | while read file; do
                size=$(du -h "$file" | cut -f1)
                echo "  - $file ($size)"
            done
        else
            echo "  （ファイルなし - ./split_video.sh で動画を分割してください）"
        fi
        
        echo ""
        echo "📝 分割SRTファイル:"
        srt_count=$(find split/output -name "*_editable.srt" -type f 2>/dev/null | wc -l)
        if [ $srt_count -gt 0 ]; then
            find split/output -name "*_editable.srt" -type f 2>/dev/null | while read file; do
                lines=$(wc -l < "$file" 2>/dev/null)
                echo "  - $file ($lines lines)"
            done
        else
            echo "  （ファイルなし - ./split_workflow.sh generate を実行してください）"
        fi
        
        echo ""
        echo "📝 統合されたSRTファイル:"
        merged_count=$(find output -name "*_merged_editable.srt" -type f 2>/dev/null | wc -l)
        if [ $merged_count -gt 0 ]; then
            find output -name "*_merged_editable.srt" -type f 2>/dev/null | while read file; do
                lines=$(wc -l < "$file" 2>/dev/null)
                echo "  - $file ($lines lines)"
            done
        else
            echo "  （ファイルなし - ./split_workflow.sh combine を実行してください）"
        fi
        
        echo ""
        echo "📊 サマリー:"
        echo "  🎬 分割動画: ${video_count}個"
        echo "  📝 分割SRT: ${srt_count}個"
        echo "  🔗 統合SRT: ${merged_count}個"
        ;;
    
    *)
        show_help
        ;;
esac
