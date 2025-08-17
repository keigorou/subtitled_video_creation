#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import glob
import argparse
from pathlib import Path

def parse_arguments():
    """引数解析"""
    parser = argparse.ArgumentParser(description='SRTファイルから引数指定でスタイル付き動画作成')
    
    parser.add_argument('--size', type=int, default=24, help='フォントサイズ')
    parser.add_argument('--color', default='white', help='文字色 (white, red, blue, green, yellow)')
    parser.add_argument('--bold', default='false', help='太字 (true/false)')
    parser.add_argument('--italic', default='false', help='斜体 (true/false)')
    parser.add_argument('--outline', type=int, default=2, help='アウトライン幅')
    parser.add_argument('--position', default='bottom', help='位置 (bottom, top, center)')
    parser.add_argument('--margin', type=int, default=40, help='マージン')
    
    return parser.parse_args()

def color_to_hex(color_name):
    """色名をFFmpeg用16進数に変換"""
    colors = {
        'white': '&H00FFFFFF',
        'red': '&H000000FF',     # BGR: 0000FF (赤)
        'blue': '&H00FF0000',    # BGR: FF0000 (青)
        'green': '&H0000FF00',   # BGR: 00FF00 (緑)
        'yellow': '&H0000FFFF',  # BGR: 00FFFF (黄)
        'black': '&H00000000',   # BGR: 000000 (黒)
        'cyan': '&H00FFFF00',    # BGR: FFFF00 (シアン)
        'magenta': '&H00FF00FF'  # BGR: FF00FF (マゼンタ)
    }
    return colors.get(color_name.lower(), '0xFFFFFF')

def create_styled_video():
    """SRTからスタイル付き動画を作成"""
    
    args = parse_arguments()
    
    print("🎬 SRTからスタイル付き動画作成")
    print(f"📏 サイズ: {args.size}")
    print(f"🎨 色: {args.color}")
    print(f"💪 太字: {args.bold}")
    print(f"📐 斜体: {args.italic}")
    print(f"🖼️ アウトライン: {args.outline}")
    print(f"📍 位置: {args.position}")
    print(f"📏 マージン: {args.margin}")
    
    # ディレクトリ作成
    os.makedirs("merged_videos", exist_ok=True)
    
    # 動画ファイルを検索
    video_files = []
    for ext in ['mp4', 'avi', 'mkv', 'mov']:
        video_files.extend(glob.glob(f"videos/*.{ext}"))
    
    if not video_files:
        print("❌ 動画ファイルが見つかりません")
        return
    
    # SRTファイルを検索
    srt_files = glob.glob("output/*.srt")
    
    if not srt_files:
        print("❌ SRTファイルが見つかりません")
        return
    
    print(f"\n📹 動画ファイル: {len(video_files)}個")
    print(f"📝 SRTファイル: {len(srt_files)}個")
    
    processed_count = 0
    
    # 各動画に対して処理
    for video_file in video_files:
        video_name = os.path.splitext(os.path.basename(video_file))[0]
        
        # 対応するSRTファイルを探す
        matching_srt = find_matching_srt(video_name, srt_files)
        
        if not matching_srt:
            print(f"⚠️ {video_name} に対応するSRTが見つかりません")
            continue
        
        # 出力ファイル名
        style_suffix = f"s{args.size}_{args.color}"
        if args.bold == 'true':
            style_suffix += "_bold"
        if args.italic == 'true':
            style_suffix += "_italic"
        
        output_file = f"merged_videos/{video_name}_{style_suffix}_styled.mp4"
        
        print(f"\n🔄 処理中: {video_name}")
        print(f"  📹 動画: {video_file}")
        print(f"  📝 字幕: {matching_srt}")
        
        # FFmpegでスタイル付き字幕を合成
        success = merge_with_style(video_file, matching_srt, output_file, args)
        
        if success:
            size = os.path.getsize(output_file) / (1024*1024)
            print(f"  ✅ 成功: {os.path.basename(output_file)} ({size:.1f} MB)")
            processed_count += 1
        else:
            print(f"  ❌ 失敗: {os.path.basename(output_file)}")
    
    print(f"\n🎉 処理完了: {processed_count}個のスタイル付き動画を作成")

def find_matching_srt(video_name, srt_files):
    """動画に対応するSRTファイルを検索"""
    
    for srt_file in srt_files:
        srt_name = os.path.splitext(os.path.basename(srt_file))[0]
        
        # 完全一致または部分一致
        if video_name == srt_name or video_name in srt_name or srt_name in video_name:
            return srt_file
    
    return None

def merge_with_style(video_file, srt_file, output_file, args):
    """FFmpegでスタイル付き字幕を合成"""
    
    try:
        # 色を16進数に変換
        color_hex = color_to_hex(args.color)
        
        # 位置の設定
        alignment = 2  # bottom
        if args.position == 'top':
            alignment = 8
        elif args.position == 'center':
            alignment = 5
        
        # スタイル文字列を構築
        style_options = [
            f"FontSize={args.size}",
            f"PrimaryColour={color_hex}",
            f"OutlineColour=0x000000",
            f"Outline={args.outline}",
            f"Alignment={alignment}",
            f"MarginV={args.margin}"
        ]
        
        # 太字・斜体の設定
        if args.bold == 'true':
            style_options.append("Bold=1")
        if args.italic == 'true':
            style_options.append("Italic=1")
        
        force_style = ','.join(style_options)
        
        # FFmpegコマンド
        cmd = [
            'ffmpeg', '-y',
            '-i', video_file,
            '-vf', f"subtitles={srt_file}:force_style='{force_style}'",
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            output_file
        ]
        
        print(f"  🔧 スタイル: {force_style}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode == 0:
            return True
        else:
            print(f"  📝 FFmpegエラー: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ⏰ タイムアウト")
        return False
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False

if __name__ == "__main__":
    create_styled_video()
