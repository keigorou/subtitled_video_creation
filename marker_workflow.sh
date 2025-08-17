#!/bin/bash

echo "🎨 マーカー付き字幕ワークフロー"
echo ""

show_help() {
    echo "使用方法: ./marker_workflow.sh [ステップ]"
    echo ""
    echo "ステップ:"
    echo "  1. generate   - 基本字幕を生成（SRT + ASS）"
    echo "  2. edit       - SRTファイルを編集（手動）"
    echo "  3. process    - マーカーを処理してASS変換"
    echo "  4. apply      - 字幕を動画に合成"
    echo "  list          - 利用可能なファイルを表示"
    echo ""
    echo "例:"
    echo "  ./marker_workflow.sh generate"
    echo "  ./marker_workflow.sh list"
    echo "  ./marker_workflow.sh edit"
}

mkdir -p videos output marker_output final_videos

case "$1" in
    "generate"|"1")
        echo "📍 Step 1: 基本字幕を生成（SRT + ASS）"
        docker-compose -f docker-compose.yml up generate-youtube
        echo ""
        echo "✅ Step 1 完了"
        echo ""
        echo "📁 生成されたファイル:"
        ls -la output/*_editable.srt 2>/dev/null | while read line; do echo "  📝 $line"; done
        ls -la output/*_styled.ass 2>/dev/null | while read line; do echo "  ✨ $line"; done
        ls -la output/*.txt 2>/dev/null | while read line; do echo "  📄 $line"; done
        echo ""
        echo "📝 次は以下のコマンドでファイルを編集してください:"
        echo "   ./marker_workflow.sh edit"
        ;;
    "list")
        echo "📁 利用可能なファイル:"
        echo ""
        echo "📝 編集可能なSRTファイル（マーカー追加用）:"
        find output -name "*_editable.srt" -type f 2>/dev/null | while read file; do
            echo "  - $file"
        done
        echo ""
        echo "✨ スタイル適用済みASSファイル:"
        find output -name "*_styled.ass" -type f 2>/dev/null | while read file; do
            echo "  - $file"
        done
        echo ""
        echo "�� テキストファイル:"
        find output -name "*.txt" -type f 2>/dev/null | while read file; do
            echo "  - $file"
        done
        ;;
    "edit"|"2")
        echo "📍 Step 2: SRTファイルを編集"
        echo ""
        echo "📝 編集可能なSRTファイル:"
        find output -name "*_editable.srt" -type f 2>/dev/null | while read file; do
            echo "  - $file"
        done
        echo ""
        echo "📝 マーカーの追加方法:"
        echo "  皆さん、¥¥¥large-blue¥¥¥こんにちは！¥¥¥私は元気です。"
        echo ""
        echo "利用可能なマーカー:"
        echo "  サイズ: large, small"
        echo "  色: blue, red, green, yellow"
        echo "  スタイル: bold, italic"
        echo "  組み合わせ: large-blue, red-bold など"
        echo ""
        echo "編集コマンド例:"
        first_srt=$(find output -name "*_editable.srt" -type f 2>/dev/null | head -1)
        if [ -n "$first_srt" ]; then
            echo "  nano $first_srt"
        else
            echo "  nano output/your_video_editable.srt"
        fi
        echo ""
        echo "編集後は以下のコマンドで続行:"
        echo "  ./marker_workflow.sh process"
        ;;
    "process"|"3")
        echo "📍 Step 3: マーカーを処理"
        
        # マーカー付きSRTファイルがあるかチェック
        marker_files=$(find output -name "*_editable.srt" -type f -exec grep -l "¥¥¥" {} \; 2>/dev/null)
        
        if [ -z "$marker_files" ]; then
            echo "❌ マーカー付きSRTファイルが見つかりません"
            echo "📝 まず _editable.srt ファイルを編集してマーカーを追加してください"
            echo "   ./marker_workflow.sh edit"
            exit 1
        fi
        
        echo "🔍 マーカー付きファイルを発見:"
        echo "$marker_files" | while read file; do
            echo "  - $file"
        done
        
        docker-compose -f docker-compose.yml run --rm generate-subtitles-with-marker python process_markers.py ./output ./marker_output
        echo "✅ Step 3 完了"
        echo "📝 次は以下のコマンドで動画に合成:"
        echo "   ./marker_workflow.sh apply"
        ;;
    "apply"|"4")
        echo "📍 Step 4: 字幕を動画に合成"
        
        # 使用する字幕ファイルの種類を確認
        marker_files=$(find marker_output -name "*_markers.ass" -type f 2>/dev/null | wc -l)
        styled_files=$(find output -name "*_styled.ass" -type f 2>/dev/null | wc -l)
        
        if [ $marker_files -gt 0 ]; then
            echo "🎨 マーカー処理済みASS字幕を使用"
            subtitle_dir="./marker_output"
        elif [ $styled_files -gt 0 ]; then
            echo "✨ スタイル適用済みASS字幕を使用"
            subtitle_dir="./output"
        else
            echo "❌ 使用可能な字幕ファイルが見つかりません"
            exit 1
        fi
        
        # 字幕合成の実行
        docker-compose -f docker-compose.yml run --rm apply-subtitles-with-marker python apply_subtitles.py
        
        echo "✅ Step 4 完了"
        echo "🎉 すべて完了！ merged_videos/ を確認してください"
        
        # 結果表示
        echo ""
        echo "📁 生成された字幕付き動画:"
        find merged_videos -name "*.mp4" -type f 2>/dev/null | while read file; do
            size=$(du -h "$file" 2>/dev/null | cut -f1)
            echo "  - $file ($size)"
        done
        ;;
    *)
        show_help
        ;;
esac
