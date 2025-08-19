#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import argparse
from pathlib import Path

def parse_arguments():
    """引数解析"""
    parser = argparse.ArgumentParser(description='マーカー処理（スタイル引数対応）')
    
    # 基本引数
    parser.add_argument('input_dir', help='入力ディレクトリ')
    parser.add_argument('output_dir', help='出力ディレクトリ')
    
    # スタイル引数
    parser.add_argument('--size', type=int, default=24, help='フォントサイズ')
    parser.add_argument('--color', default='white', help='文字色')
    parser.add_argument('--bold', action='store_true', help='太字にする')
    parser.add_argument('--italic', action='store_true', help='斜体にする')
    parser.add_argument('--outline', type=int, default=2, help='アウトライン幅')
    parser.add_argument('--position', default='bottom', help='位置')
    parser.add_argument('--margin', type=int, default=40, help='マージン')
    parser.add_argument('--font', default='Noto Sans CJK JP', help='フォント名')
    # 背景オプションを追加
    parser.add_argument('--background', default='none', help='背景色 (black, white, gray, none)')
    parser.add_argument('--background-alpha', type=float, default=0.8, help='背景透明度 (0.0-1.0)')
    
    return parser.parse_args()

def color_to_ass_bgr(color_name):
    """色名をASS BGR形式に変換"""
    colors = {
        'white': '&H00FFFFFF',
        'red': '&H000000FF',
        'blue': '&H00FF0000',
        'green': '&H0000FF00',
        'yellow': '&H0000FFFF',
        'black': '&H00000000',
        'cyan': '&H00FFFF00',
        'magenta': '&H00FF00FF',
        'gray': '&H00808080'
    }
    return colors.get(color_name.lower(), '&H00FFFFFF')

def position_to_alignment(position):
    """位置をASS alignment値に変換"""
    positions = {
        'bottom': 2,
        'center': 5,
        'top': 8
    }
    return positions.get(position.lower(), 2)

def parse_marker(marker_text):
    """マーカーテキストを解析してスタイル情報を抽出（数値サイズ対応版）"""
    
    # デフォルト値
    style = {
        'fontsize': None,
        'color': None,
        'bold': None,
        'italic': None
    }
    
    # マーカーを小文字で処理
    marker_lower = marker_text.lower()
    
    print(f"    🔍 マーカー解析: '{marker_text}' -> '{marker_lower}'")
    
    # サイズの処理（数値指定を優先）
    # size数値パターン（例：size48, size32）
    size_match = re.search(r'size(\d+)', marker_lower)
    if size_match:
        style['fontsize'] = int(size_match.group(1))
        print(f"      📏 数値サイズ指定: {style['fontsize']}")
    else:
        # 従来のlarge/smallパターン
        if 'large' in marker_lower:
            style['fontsize'] = 36
            print(f"      📏 large -> 36")
        elif 'small' in marker_lower:
            style['fontsize'] = 18
            print(f"      📏 small -> 18")
    
    # 色の処理（従来通り）
    if 'red' in marker_lower:
        style['color'] = 'red'
        print(f"      🎨 色: red")
    elif 'blue' in marker_lower:
        style['color'] = 'blue'
        print(f"      🎨 色: blue")
    elif 'green' in marker_lower:
        style['color'] = 'green'
        print(f"      🎨 色: green")
    elif 'yellow' in marker_lower:
        style['color'] = 'yellow'
        print(f"      🎨 色: yellow")
    elif 'white' in marker_lower:
        style['color'] = 'white'
        print(f"      🎨 色: white")
    elif 'black' in marker_lower:
        style['color'] = 'black'
        print(f"      🎨 色: black")
    
    # スタイルの処理（従来通り）
    if 'bold' in marker_lower:
        style['bold'] = 1
        print(f"      💪 太字")
    
    if 'italic' in marker_lower:
        style['italic'] = 1
        print(f"      📐 斜体")
    
    print(f"      ✅ 解析結果: {style}")
    return style

def process_srt_with_markers(srt_content, default_style_args):
    """SRTファイルのマーカーを処理（デバッグ強化版）"""
    
    # マーカーパターン: ¥¥¥marker¥¥¥text¥¥¥
    marker_pattern = r'¥¥¥([^¥]+)¥¥¥([^¥]*)¥¥¥'
    
    def replace_marker(match):
        marker_text = match.group(1)
        content = match.group(2)
        
        print(f"  🎯 マーカー発見: '{marker_text}' 適用対象: '{content}'")
        print(f"  📋 使用するデフォルト設定: size={default_style_args['size']}, color={default_style_args['color']}, bold={default_style_args['bold']}, italic={default_style_args['italic']}")
        
        style = parse_marker(marker_text)
        
        # ASSタグに変換
        tags = []
        
        if style['fontsize']:
            tags.append(f"\\fs{style['fontsize']}")
            print(f"      📏 マーカーサイズタグ: \\fs{style['fontsize']}")
        
        if style['color']:
            # 色名からASSタグに変換
            if style['color'] == 'red':
                tags.append(r'\c&H0000FF&')
            elif style['color'] == 'blue':
                tags.append(r'\c&HFF0000&')
            elif style['color'] == 'green':
                tags.append(r'\c&H00FF00&')
            elif style['color'] == 'yellow':
                tags.append(r'\c&H00FFFF&')
            elif style['color'] == 'white':
                tags.append(r'\c&HFFFFFF&')
            elif style['color'] == 'black':
                tags.append(r'\c&H000000&')
            print(f"      🎨 マーカー色タグ: 最後に追加されたタグ")
        
        if style['bold']:
            tags.append(r'\b1')
            print(f"      💪 マーカー太字タグ: \\b1")
        
        if style['italic']:
            tags.append(r'\i1')
            print(f"      📐 マーカー斜体タグ: \\i1")
        
        # タグを組み合わせ
        if tags:
            start_tag = '{' + ''.join(tags) + '}'
            print(f"      🏁 完成したマーカータグ: '{start_tag}'")
            
            # 明示的にDefaultスタイルに戻すタグを作成
            default_reset_tags = []
            
            # デフォルトのフォントサイズに戻す
            default_reset_tags.append(f"\\fs{default_style_args['size']}")
            print(f"      📏 リセットサイズタグ: \\fs{default_style_args['size']}")
            
            # デフォルトの色に戻す
            default_color = default_style_args['color'].lower()
            if default_color == 'red':
                default_reset_tags.append(r'\c&H0000FF&')
            elif default_color == 'blue':
                default_reset_tags.append(r'\c&HFF0000&')
            elif default_color == 'green':
                default_reset_tags.append(r'\c&H00FF00&')
            elif default_color == 'yellow':
                default_reset_tags.append(r'\c&H00FFFF&')
            elif default_color == 'white':
                default_reset_tags.append(r'\c&HFFFFFF&')
            elif default_color == 'black':
                default_reset_tags.append(r'\c&H000000&')
            else:
                default_reset_tags.append(r'\c&HFFFFFF&')  # フォールバック
            print(f"      🎨 リセット色タグ: 追加完了 ({default_color})")
            
            # デフォルトの太字・斜体設定に戻す
            if default_style_args.get('bold', False):
                default_reset_tags.append(r'\b1')
                print(f"      💪 リセット太字タグ: \\b1 (太字を維持)")
            else:
                default_reset_tags.append(r'\b0')
                print(f"      💪 リセット太字タグ: \\b0 (太字を解除)")
                
            if default_style_args.get('italic', False):
                default_reset_tags.append(r'\i1')
                print(f"      📐 リセット斜体タグ: \\i1 (斜体を維持)")
            else:
                default_reset_tags.append(r'\i0')
                print(f"      📐 リセット斜体タグ: \\i0 (斜体を解除)")
            
            reset_tag = '{' + ''.join(default_reset_tags) + '}'
            
            result = f"{start_tag}{content}{reset_tag}"
            print(f"    ✨ 最終変換結果: '{result}'")
            print(f"    🔄 完成したリセットタグ: '{reset_tag}'")
            print(f"    📊 期待される動作:")
            print(f"       マーカー部分「{content}」のサイズ: {style.get('fontsize', 'デフォルト')}")
            print(f"       リセット後のサイズ: {default_style_args['size']}")
            return result
        else:
            print(f"    ⚠️ スタイルが適用されませんでした")
            return content
    
    # マーカーを置換
    processed_content = re.sub(marker_pattern, replace_marker, srt_content)
    
    return processed_content

def srt_to_ass_with_style(srt_content, video_name, args):
    """SRTをスタイル適用済みASSに変換"""
    
    # 色とアライメントを変換
    primary_color = color_to_ass_bgr(args.color)
    alignment = position_to_alignment(args.position)
    bold_value = 1 if args.bold else 0
    italic_value = 1 if args.italic else 0
    
    print(f"🎨 適用するデフォルトスタイル:")
    print(f"  📏 サイズ: {args.size}")
    print(f"  🎨 色: {args.color} -> {primary_color}")
    print(f"  💪 太字: {bold_value}")
    print(f"  📐 斜体: {italic_value}")
    print(f"  🖼️ アウトライン: {args.outline}")
    print(f"  📍 位置: {args.position} -> {alignment}")
    print(f"  📏 マージン: {args.margin}")
    print(f"  🔤 フォント: {args.font}")
    print(f"  🎯 背景: {args.background}")
    if args.background != 'none':
        print(f"  👻 背景透明度: {args.background_alpha}")
    
    # 背景色の設定
    back_color = "&H80000000"  # デフォルト（半透明黒）
    border_style = 1  # デフォルト（アウトラインのみ）
    
    if args.background != 'none':
        background_color_hex = color_to_ass_bgr(args.background)
        # 透明度を考慮
        alpha_value = int(args.background_alpha * 255)
        back_color = f"&H{alpha_value:02X}{background_color_hex[3:]}"
        border_style = 4  # 背景ボックスを有効
        print(f"  🎨 背景色設定: {back_color}")
    
    # ASSヘッダー（スタイル適用済み）
    ass_header = f"""[Script Info]
Title: {video_name}
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{args.font},{args.size},{primary_color},&H000000FF,&H00000000,{back_color},{bold_value},{italic_value},0,0,100,100,0,0,{border_style},{args.outline},2,{alignment},30,30,{args.margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # SRTを解析してASSイベントに変換
    events = []
    lines = srt_content.strip().split('\n\n')
    
    for block in lines:
        lines_in_block = block.strip().split('\n')
        if len(lines_in_block) >= 3:
            # 番号をスキップ
            time_line = lines_in_block[1]
            text_lines = lines_in_block[2:]
            
            # 時間を解析
            if ' --> ' in time_line:
                start_time, end_time = time_line.split(' --> ')
                start_ass = srt_time_to_ass_time(start_time.strip())
                end_ass = srt_time_to_ass_time(end_time.strip())
                
                # テキストを結合
                text = ' '.join(text_lines)
                
                # イベント行を作成
                event = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}"
                events.append(event)
    
    final_ass = ass_header + '\n'.join(events)
    
    return final_ass

def srt_time_to_ass_time(srt_time):
    """SRT時間形式をASS時間形式に変換"""
    # SRT: 00:01:23,456
    # ASS: 0:01:23.45
    
    time_part, ms_part = srt_time.split(',')
    hours, minutes, seconds = time_part.split(':')
    
    # ミリ秒を100分の1秒に変換
    centiseconds = int(ms_part) // 10
    
    return f"{int(hours)}:{minutes}:{seconds}.{centiseconds:02d}"

def process_markers_in_directory(args):
    """ディレクトリ内のマーカー付きSRTファイルを処理（スタイル適用）"""
    
    input_dir = args.input_dir
    output_dir = args.output_dir
    
    print(f"🔍 マーカー処理開始（スタイル適用）")
    print(f"📁 入力: {input_dir}")
    print(f"📁 出力: {output_dir}")
    
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    
    processed_count = 0
    
    # 入力ディレクトリ内のSRTファイルを検索
    for filename in os.listdir(input_dir):
        if filename.endswith('.srt'):
            input_path = os.path.join(input_dir, filename)
            
            print(f"\n📝 処理中: {filename}")
            
            try:
                # ファイルを読み込み
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # マーカーがあるかチェック
                if '¥¥¥' not in content:
                    print(f"  ⚠️ マーカーが見つかりません - スキップ")
                    continue
                
                print(f"  🎨 マーカーを発見 - 処理中...")
                
                # デフォルトスタイルの情報を渡す
                default_style = {
                    'size': args.size,
                    'color': args.color,
                    'bold': args.bold,
                    'italic': args.italic
                }
                
                print(f"  🔄 デフォルトスタイル設定: {default_style}")
                
                # マーカーを処理
                processed_content = process_srt_with_markers(content, default_style)
                
                # スタイル適用済みASSに変換
                base_name = os.path.splitext(filename)[0]
                video_name = base_name.replace('_editable', '')
                ass_content = srt_to_ass_with_style(processed_content, video_name, args)
                
                # ファイル名を生成（スタイル情報を含む）
                style_suffix = f"s{args.size}_{args.color}"
                if args.bold:
                    style_suffix += "_bold"
                if args.italic:
                    style_suffix += "_italic"
                if args.background != 'none':
                    style_suffix += f"_bg{args.background}"
                
                if filename.endswith('_editable.srt'):
                    ass_filename = filename.replace('_editable.srt', f'_markers_{style_suffix}.ass')
                else:
                    ass_filename = f"{base_name}_markers_{style_suffix}.ass"
                
                # 出力ファイルパス
                output_path = os.path.join(output_dir, ass_filename)
                
                # ASSファイルを書き出し
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(ass_content)
                
                file_size = os.path.getsize(output_path)
                print(f"  ✅ 完了: {ass_filename} ({file_size} bytes)")
                processed_count += 1
                
            except Exception as e:
                print(f"  ❌ エラー: {e}")
                import traceback
                traceback.print_exc()
    
    print(f"\n🎉 処理完了: {processed_count}個のスタイル適用済みマーカーASSファイルを作成")

def main():
    """メイン処理"""
    
    args = parse_arguments()
    
    if not os.path.exists(args.input_dir):
        print(f"❌ 入力ディレクトリが見つかりません: {args.input_dir}")
        sys.exit(1)
    
    process_markers_in_directory(args)

if __name__ == "__main__":
    main()
