#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
from pathlib import Path

def parse_marker(marker_text):
   """マーカーテキストを解析してスタイル情報を抽出"""
   
   # デフォルト値
   style = {
       'fontsize': 24,
       'color': '&H00FFFFFF',  # 白
       'bold': 0,
       'italic': 0
   }
   
   # マーカーを小文字で処理
   marker_lower = marker_text.lower()
   
   # サイズの処理
   if 'large' in marker_lower:
       style['fontsize'] = 36
   elif 'small' in marker_lower:
       style['fontsize'] = 18
   
   # 色の処理 (BGR形式)
   if 'red' in marker_lower:
       style['color'] = '&H000000FF'  # 赤
   elif 'blue' in marker_lower:
       style['color'] = '&H00FF0000'  # 青
   elif 'green' in marker_lower:
       style['color'] = '&H0000FF00'  # 緑
   elif 'yellow' in marker_lower:
       style['color'] = '&H0000FFFF'  # 黄色
   
   # スタイルの処理
   if 'bold' in marker_lower:
       style['bold'] = 1
   
   if 'italic' in marker_lower:
       style['italic'] = 1
   
   return style

def process_srt_with_markers(srt_content):
   """SRTファイルのマーカーを処理"""
   
   # マーカーパターン: ¥¥¥marker¥¥¥text¥¥¥
   marker_pattern = r'¥¥¥([^¥]+)¥¥¥([^¥]*)¥¥¥'
   
   def replace_marker(match):
       marker_text = match.group(1)
       content = match.group(2)
       
       style = parse_marker(marker_text)
       
       # ASSタグに変換
       tags = []
       
       if style['fontsize'] != 24:
           tags.append(f"\\fs{style['fontsize']}")
       
       if style['color'] != '&H00FFFFFF':
           # BGRからRGBに変換してHTMLカラーコードにする簡易版
           if style['color'] == '&H000000FF':  # 赤
               tags.append(r'\c&H0000FF&')
           elif style['color'] == '&H00FF0000':  # 青
               tags.append(r'\c&HFF0000&')
           elif style['color'] == '&H0000FF00':  # 緑
               tags.append(r'\c&H00FF00&')
           elif style['color'] == '&H0000FFFF':  # 黄色
               tags.append(r'\c&H00FFFF&')
       
       if style['bold']:
           tags.append(r'\b1')
       
       if style['italic']:
           tags.append(r'\i1')
       
       # タグを組み合わせ
       if tags:
           start_tag = '{' + ''.join(tags) + '}'
           end_tag = r'{\r}' if tags else ''
           return f"{start_tag}{content}{end_tag}"
       else:
           return content
   
   # マーカーを置換
   processed_content = re.sub(marker_pattern, replace_marker, srt_content)
   
   return processed_content

def srt_to_ass(srt_content, video_name):
   """SRTをASSに変換"""
   
   # ASSヘッダー
   ass_header = f"""[Script Info]
Title: {video_name}
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK JP,24,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,30,30,40,1

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
   
   return ass_header + '\n'.join(events)

def srt_time_to_ass_time(srt_time):
   """SRT時間形式をASS時間形式に変換"""
   # SRT: 00:01:23,456
   # ASS: 0:01:23.45
   
   time_part, ms_part = srt_time.split(',')
   hours, minutes, seconds = time_part.split(':')
   
   # ミリ秒を100分の1秒に変換
   centiseconds = int(ms_part) // 10
   
   return f"{int(hours)}:{minutes}:{seconds}.{centiseconds:02d}"

def process_markers_in_directory(input_dir, output_dir):
   """ディレクトリ内のマーカー付きSRTファイルを処理"""
   
   print(f"🔍 マーカー処理開始")
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
               
               # マーカーを処理
               processed_content = process_srt_with_markers(content)
               
               # ASSに変換
               base_name = os.path.splitext(filename)[0]
               video_name = base_name.replace('_editable', '')
               ass_content = srt_to_ass(processed_content, video_name)
               
               # ファイル名を生成
               if filename.endswith('_editable.srt'):
                   ass_filename = filename.replace('_editable.srt', '_markers.ass')
               else:
                   ass_filename = f"{base_name}_markers.ass"
               
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
   
   print(f"\n🎉 処理完了: {processed_count}個のマーカー付きASSファイルを作成")

def main():
   """メイン処理"""
   
   if len(sys.argv) != 3:
       print("使用方法: python process_markers.py <入力ディレクトリ> <出力ディレクトリ>")
       print("例: python process_markers.py ./output ./marker_output")
       sys.exit(1)
   
   input_dir = sys.argv[1]
   output_dir = sys.argv[2]
   
   if not os.path.exists(input_dir):
       print(f"❌ 入力ディレクトリが見つかりません: {input_dir}")
       sys.exit(1)
   
   process_markers_in_directory(input_dir, output_dir)

if __name__ == "__main__":
   main()
