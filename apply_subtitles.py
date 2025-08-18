import os
import subprocess
import shutil
import glob
from pathlib import Path
import sys
import re

def apply_subtitles_to_videos(video_dir="/input_videos", subtitle_dir="/input_subtitles", output_dir="/output"):
   """字幕を動画に自動合成（マーカー保持版・背景対応）"""
   
   print("🎬 字幕を動画に自動合成（マーカー保持版・背景対応）")
   print(f"📁 動画ディレクトリ: {video_dir}")
   print(f"📄 字幕ディレクトリ: {subtitle_dir}")
   print(f"📁 出力ディレクトリ: {output_dir}")
   
   # コマンドライン引数から追加のスタイルパラメータを取得
   style_args = parse_style_args()
   
   os.makedirs(output_dir, exist_ok=True)
   work_dir = "/tmp/subtitle_merge_work"
   os.makedirs(work_dir, exist_ok=True)
   
   # 動画ファイル検索
   video_files = []
   video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
   
   for ext in video_extensions:
       files = glob.glob(os.path.join(video_dir, f"*{ext}"))
       files.extend(glob.glob(os.path.join(video_dir, f"*{ext.upper()}")))
       video_files.extend(files)
   
   if not video_files:
       print("❌ 動画ファイルが見つかりません")
       return
   
   # 字幕ファイル検索
   subtitle_files = []
   subtitle_extensions = ['.ass', '.srt']
   
   for ext in subtitle_extensions:
       files = glob.glob(os.path.join(subtitle_dir, f"*{ext}"))
       subtitle_files.extend(files)
   
   if not subtitle_files:
       print("❌ 字幕ファイルが見つかりません")
       return
   
   print(f"\n📹 動画ファイル: {len(video_files)}個")
   print(f"📝 字幕ファイル: {len(subtitle_files)}個")
   
   processed_count = 0
   
   # 動画と字幕のマッチング処理
   for video_file in video_files:
       video_filename = os.path.basename(video_file)
       base_name = os.path.splitext(video_filename)[0]
       
       # 対応する字幕ファイルを探す
       matching_subtitles = find_matching_subtitles(base_name, subtitle_files)
       
       if not matching_subtitles:
           print(f"⚠️ {video_filename} に対応する字幕ファイルが見つかりません")
           continue
       
       try:
           for subtitle_file in matching_subtitles:
               subtitle_filename = os.path.basename(subtitle_file)
               subtitle_ext = Path(subtitle_file).suffix.lower()
               
               print(f"\n🎬 処理中: {video_filename} + {subtitle_filename}")
               
               # マーカー付きASSファイルかチェック
               has_markers = check_for_markers(subtitle_file) if subtitle_ext == '.ass' else False
               
               if has_markers:
                   print(f"  🎨 マーカー付きASSファイル検出")
               
               # スタイル強制適用が必要かチェック
               if style_args and len(style_args) > 0:
                   print(f"  🎨 スタイル強制適用モード")
                   
                   if subtitle_ext == '.ass':
                       if has_markers:
                           # マーカー付きASSの場合：マーカーを保持してSRTに変換
                           print(f"  🔄 マーカー保持ASS→SRT変換中...")
                           temp_srt = os.path.join(work_dir, f"marker_temp_{hash(subtitle_file) % 10000}.srt")
                           
                           if convert_ass_to_srt_with_markers(subtitle_file, temp_srt, style_args):
                               subtitle_file_to_use = temp_srt
                               print(f"  ✅ マーカー保持変換成功")
                           else:
                               print(f"  ❌ マーカー保持変換失敗、通常変換を試行")
                               temp_srt = os.path.join(work_dir, f"temp_{hash(subtitle_file) % 10000}.srt")
                               if convert_ass_to_srt(subtitle_file, temp_srt):
                                   subtitle_file_to_use = temp_srt
                               else:
                                   subtitle_file_to_use = subtitle_file
                       else:
                           # 通常のASS→SRT変換
                           print(f"  🔄 ASS→SRT変換中...")
                           temp_srt = os.path.join(work_dir, f"temp_{hash(subtitle_file) % 10000}.srt")
                           
                           if convert_ass_to_srt(subtitle_file, temp_srt):
                               subtitle_file_to_use = temp_srt
                               print(f"  ✅ ASS→SRT変換成功")
                           else:
                               subtitle_file_to_use = subtitle_file
                   else:
                       subtitle_file_to_use = subtitle_file
                   
               else:
                   # スタイル引数なし、元のファイルをそのまま使用
                   subtitle_file_to_use = subtitle_file
               
               # 出力ファイル名を生成
               style_suffix = ""
               if style_args:
                   if 'size' in style_args:
                       style_suffix += f"_s{style_args['size']}"
                   if 'color' in style_args:
                       style_suffix += f"_{style_args['color']}"
                   if 'bold' in style_args:
                       style_suffix += "_bold"
                   if 'background' in style_args and style_args['background'] != 'none':
                       style_suffix += f"_bg{style_args['background']}"
               
               subtitle_base = os.path.splitext(subtitle_filename)[0]
               if has_markers:
                   output_filename = f"{base_name}_{subtitle_base}_markers{style_suffix}_merged.mp4"
               else:
                   output_filename = f"{base_name}_{subtitle_base}{style_suffix}_merged.mp4"
               
               output_path = os.path.join(output_dir, output_filename)
               
               # FFmpegコマンドを実行
               success = merge_subtitle_with_ffmpeg(video_file, subtitle_file_to_use, output_path, style_args, has_markers)
               
               if success:
                   file_size = os.path.getsize(output_path)
                   print(f"  ✅ 成功: {output_filename}")
                   print(f"  📊 サイズ: {file_size / (1024*1024):.1f} MB")
                   processed_count += 1
               else:
                   print(f"  ❌ 失敗: {output_filename}")
               
               # 一時ファイルをクリーンアップ
               for temp_file in [f for f in [locals().get('temp_srt')] if f and os.path.exists(f)]:
                   os.remove(temp_file)
                       
       except Exception as e:
           print(f"  ❌ エラー ({video_filename}): {e}")
   
   print(f"\n🎉 処理完了: {processed_count}個の字幕付き動画を作成しました")

def check_for_markers(ass_file):
   """ASSファイルにマーカー（ASSタグ）が含まれているかチェック"""
   try:
       with open(ass_file, 'r', encoding='utf-8') as f:
           content = f.read()
       
       # ASSタグの存在をチェック
       marker_patterns = [r'\\fs\d+', r'\\c&H[0-9A-Fa-f]+&', r'\\b1', r'\\i1']
       
       for pattern in marker_patterns:
           if re.search(pattern, content):
               return True
       
       return False
   except:
       return False

def convert_ass_to_srt_with_markers(ass_file, srt_file, style_args):
   """マーカー情報を保持してASSファイルをSRTファイルに変換（修正版）"""
   
   try:
       with open(ass_file, 'r', encoding='utf-8') as f:
           content = f.read()
       
       # Dialogue行を抽出
       dialogue_lines = []
       for line in content.split('\n'):
           if line.startswith('Dialogue:'):
               dialogue_lines.append(line)
       
       if not dialogue_lines:
           return False
       
       print(f"    🎯 {len(dialogue_lines)}行のDialogue行を処理中...")
       
       # SRT形式に変換（マーカー情報をHTMLタグに変換）
       srt_content = ""
       marker_count = 0
       
       for i, dialogue_line in enumerate(dialogue_lines, 1):
           parts = dialogue_line.split(',', 9)
           if len(parts) >= 10:
               start_time = parts[1].strip()
               end_time = parts[2].strip()
               text = parts[9].strip()
               
               print(f"      🔍 原文: '{text}'")
               
               # ASSタグをHTMLタグに変換（修正版）
               converted_text, markers_found = convert_ass_tags_to_html_fixed(text, style_args)
               if markers_found:
                   marker_count += markers_found
               
               print(f"      ✨ 変換後: '{converted_text}'")
               
               # ASS時間をSRT時間に変換
               start_srt = ass_time_to_srt_time(start_time)
               end_srt = ass_time_to_srt_time(end_time)
               
               srt_content += f"{i}\n"
               srt_content += f"{start_srt} --> {end_srt}\n"
               srt_content += f"{converted_text}\n\n"
       
       with open(srt_file, 'w', encoding='utf-8') as f:
           f.write(srt_content)
       
       print(f"    ✅ マーカー保持変換完了: {marker_count}個のマーカーを変換")
       return True
       
   except Exception as e:
       print(f"    ❌ マーカー保持変換エラー: {e}")
       return False

def convert_ass_tags_to_html_fixed(text, style_args):
   """ASSタグをHTMLタグに変換（修正版）"""
   
   converted_text = text
   markers_found = 0
   
   print(f"        🔧 変換開始: '{converted_text}'")
   
   # Step 1: 完全なASSタグブロック（{...}）を処理
   def process_ass_tag_block(match):
       nonlocal markers_found
       tag_content = match.group(1)
       print(f"        🎯 タグブロック発見: '{tag_content}'")
       
       html_tags = []
       
       # フォントサイズ
       fs_match = re.search(r'\\fs(\d+)', tag_content)
       if fs_match:
           size = fs_match.group(1)
           html_tags.append(f'<font size="{size}">')
           markers_found += 1
           print(f"          📏 フォントサイズ: {size}")
       
       # 色
       color_match = re.search(r'\\c&H([0-9A-Fa-f]+)&', tag_content)
       if color_match:
           bgr_hex = color_match.group(1)
           rgb_hex = bgr_to_rgb_hex(bgr_hex)
           html_tags.append(f'<font color="#{rgb_hex}">')
           markers_found += 1
           print(f"          🎨 色: {bgr_hex} -> {rgb_hex}")
       
       # 太字
       if '\\b1' in tag_content:
           html_tags.append('<b>')
           markers_found += 1
           print(f"          💪 太字")
       
       # 斜体
       if '\\i1' in tag_content:
           html_tags.append('<i>')
           markers_found += 1
           print(f"          📐 斜体")
       
       # リセット
       if '\\r' in tag_content:
           return '</font></b></i>'
       
       return ''.join(html_tags)
   
   # Step 2: ASSタグブロック（{...}）を置換
   converted_text = re.sub(r'\{([^}]*)\}', process_ass_tag_block, converted_text)
   
   print(f"        🔧 ブロック処理後: '{converted_text}'")
   
   # Step 3: 残った不完全なタグや記号をクリーンアップ
   # 余分な{や}を削除
   converted_text = re.sub(r'[{}]', '', converted_text)
   
   # 連続するHTMLタグを整理
   converted_text = re.sub(r'(<font[^>]*>)\s*(<font[^>]*>)', r'\1\2', converted_text)
   
   # 空のタグを削除
   converted_text = re.sub(r'<font[^>]*></font>', '', converted_text)
   converted_text = re.sub(r'<b></b>', '', converted_text)
   converted_text = re.sub(r'<i></i>', '', converted_text)
   
   # 先頭・末尾の空白を削除
   converted_text = converted_text.strip()
   
   print(f"        ✅ 最終結果: '{converted_text}'")
   
   return converted_text, markers_found

def bgr_to_rgb_hex(bgr_hex):
   """BGR 16進数をRGB 16進数に変換"""
   try:
       # BGRHEXからRGBに変換（例：0000FF → FF0000）
       if len(bgr_hex) == 6:
           b = bgr_hex[0:2]
           g = bgr_hex[2:4]
           r = bgr_hex[4:6]
           return f"{r}{g}{b}"
       return bgr_hex
   except:
       return "FFFFFF"

def convert_ass_to_srt(ass_file, srt_file):
   """ASSファイルをSRTファイルに変換（通常版）"""
   
   try:
       with open(ass_file, 'r', encoding='utf-8') as f:
           content = f.read()
       
       # Dialogue行を抽出
       dialogue_lines = []
       for line in content.split('\n'):
           if line.startswith('Dialogue:'):
               dialogue_lines.append(line)
       
       if not dialogue_lines:
           return False
       
       # SRT形式に変換
       srt_content = ""
       for i, dialogue_line in enumerate(dialogue_lines, 1):
           parts = dialogue_line.split(',', 9)
           if len(parts) >= 10:
               start_time = parts[1].strip()
               end_time = parts[2].strip()
               text = parts[9].strip()
               
               # ASSタグを完全に除去
               text = re.sub(r'\{[^}]*\}', '', text)
               text = re.sub(r'[{}]', '', text)  # 残った{や}も削除
               text = text.strip()
               
               # ASS時間をSRT時間に変換
               start_srt = ass_time_to_srt_time(start_time)
               end_srt = ass_time_to_srt_time(end_time)
               
               srt_content += f"{i}\n"
               srt_content += f"{start_srt} --> {end_srt}\n"
               srt_content += f"{text}\n\n"
       
       with open(srt_file, 'w', encoding='utf-8') as f:
           f.write(srt_content)
       
       return True
       
   except Exception as e:
       print(f"  ❌ ASS→SRT変換エラー: {e}")
       return False

def ass_time_to_srt_time(ass_time):
   """ASS時間をSRT時間に変換"""
   try:
       # ASS: 0:01:23.45 -> SRT: 00:01:23,450
       parts = ass_time.split(':')
       hours = int(parts[0])
       minutes = int(parts[1])
       seconds_parts = parts[2].split('.')
       seconds = int(seconds_parts[0])
       centiseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
       milliseconds = centiseconds * 10
       
       return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
   except:
       return "00:00:00,000"

def parse_style_args():
   """コマンドライン引数からスタイルパラメータを解析（背景対応版）"""
   style_args = {}
   
   args = sys.argv[1:]
   i = 0
   while i < len(args):
       if args[i] == '--size' and i + 1 < len(args):
           style_args['size'] = int(args[i + 1])
           i += 2
       elif args[i] == '--color' and i + 1 < len(args):
           style_args['color'] = args[i + 1]
           i += 2
       elif args[i] == '--bold':
           style_args['bold'] = True
           i += 1
       elif args[i] == '--italic':
           style_args['italic'] = True
           i += 1
       elif args[i] == '--outline' and i + 1 < len(args):
           style_args['outline'] = int(args[i + 1])
           i += 2
       elif args[i] == '--position' and i + 1 < len(args):
           style_args['position'] = args[i + 1]
           i += 2
       elif args[i] == '--margin' and i + 1 < len(args):
           style_args['margin'] = int(args[i + 1])
           i += 2
       elif args[i] == '--background' and i + 1 < len(args):
           style_args['background'] = args[i + 1]
           i += 2
       elif args[i] == '--background-alpha' and i + 1 < len(args):
           style_args['background_alpha'] = float(args[i + 1])
           i += 2
       else:
           i += 1
   
   if style_args:
       print(f"🎨 スタイル強制適用:")
       for key, value in style_args.items():
           print(f"  {key}: {value}")
   
   return style_args

def find_matching_subtitles(video_base_name, subtitle_files):
   """動画ベース名に対応する字幕ファイルを検索"""
   matching = []
   
   for subtitle_file in subtitle_files:
       subtitle_filename = os.path.basename(subtitle_file)
       subtitle_base = os.path.splitext(subtitle_filename)[0]
       
       # 完全一致
       if subtitle_base == video_base_name:
           matching.append(subtitle_file)
       # 部分一致
       elif subtitle_base.startswith(video_base_name + "_"):
           matching.append(subtitle_file)
       # 逆方向の一致も確認
       elif video_base_name.startswith(subtitle_base.replace('_editable', '').replace('_markers', '')):
           matching.append(subtitle_file)
   
   return matching

def color_to_bgr_hex(color_name):
   """色名をFFmpeg用BGR形式16進数に変換"""
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

def merge_subtitle_with_ffmpeg(video_path, subtitle_path, output_path, style_args=None, has_markers=False):
   """FFmpegで字幕を動画に合成（マーカー対応版・背景対応）"""
   
   try:
       if style_args and len(style_args) > 0:
           # スタイルパラメータが指定されている場合は強制適用
           print(f"  🎨 スタイル強制適用モード")
           if has_markers:
               print(f"    🎯 マーカー情報も保持")
           
           # スタイル文字列を構築
           style_options = []
           
           if 'size' in style_args:
               fontsize = style_args['size']
               style_options.append(f"FontSize={fontsize}")
               print(f"    📏 FontSize={fontsize}")
           
           if 'color' in style_args:
               color_bgr = color_to_bgr_hex(style_args['color'])
               style_options.append(f"PrimaryColour={color_bgr}")
               print(f"    🎨 PrimaryColour={color_bgr}")
           
           if 'bold' in style_args and style_args['bold']:
               style_options.append("Bold=1")
               print(f"    💪 Bold=1")
           
           if 'italic' in style_args and style_args['italic']:
               style_options.append("Italic=1")
               print(f"    📐 Italic=1")
           
           if 'outline' in style_args:
               outline = style_args['outline']
               style_options.append(f"Outline={outline}")
               style_options.append("OutlineColour=&H00000000")
               print(f"    🖼️ Outline={outline}")
           
           if 'position' in style_args:
               alignment = {'bottom': 2, 'center': 5, 'top': 8}.get(style_args['position'], 2)
               style_options.append(f"Alignment={alignment}")
               print(f"    📍 Alignment={alignment}")
           
           if 'margin' in style_args:
               margin = style_args['margin']
               style_options.append(f"MarginV={margin}")
               print(f"    📏 MarginV={margin}")
           
           # 背景色の設定
           if 'background' in style_args and style_args['background'] != 'none':
               background_color = color_to_bgr_hex(style_args['background'])
               
               # 透明度の設定
               alpha = style_args.get('background_alpha', 0.8)
               alpha_value = int(alpha * 255)
               background_with_alpha = f"&H{alpha_value:02X}{background_color[3:]}"
               
               style_options.append(f"BackColour={background_with_alpha}")
               style_options.append("BorderStyle=4")  # 背景ボックスを有効
               print(f"    🎯 BackColour={background_with_alpha}")
               print(f"    📦 BorderStyle=4 (背景ボックス有効)")
           
           force_style = ','.join(style_options)
           print(f"  🔧 最終force_style: {force_style}")
           
           # subtitlesフィルタを使用
           cmd = [
               'ffmpeg', '-y',
               '-i', video_path,
               '-vf', f"subtitles={subtitle_path}:force_style='{force_style}'",
               '-c:a', 'copy',
               '-c:v', 'libx264',
               '-preset', 'medium',
               '-crf', '23',
               output_path
           ]
       else:
           # スタイルパラメータなし、元のファイルをそのまま使用
           print(f"  📝 元のスタイル使用モード")
           
           subtitle_ext = Path(subtitle_path).suffix.lower()
           if subtitle_ext == '.ass':
               cmd = [
                   'ffmpeg', '-y',
                   '-i', video_path,
                   '-vf', f'ass={subtitle_path}',
                   '-c:a', 'copy',
                   '-c:v', 'libx264',
                   '-preset', 'medium',
                   '-crf', '23',
                   output_path
               ]
           else:
               cmd = [
                   'ffmpeg', '-y',
                   '-i', video_path,
                   '-vf', f"subtitles={subtitle_path}",
                   '-c:a', 'copy',
                   '-c:v', 'libx264',
                   '-preset', 'medium',
                   '-crf', '23',
                   output_path
               ]
       
       print(f"  🔄 FFmpeg実行中...")
       result = subprocess.run(cmd, capture_output=True, text=True)
       
       if result.returncode == 0:
           return True
       else:
           print(f"  📝 FFmpegエラー: {result.stderr}")
           return False
           
   except Exception as e:
       print(f"  📝 実行エラー: {e}")
       return False

if __name__ == "__main__":
   apply_subtitles_to_videos()
