import os
import subprocess
import shutil
import chardet

def fix_subtitle_encoding(srt_path, output_path):
    """字幕ファイルの文字エンコーディングをUTF-8に修正"""
    try:
        # ファイルのエンコーディングを検出
        with open(srt_path, 'rb') as f:
            raw_data = f.read()
            
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')
        confidence = detected.get('confidence', 0)
        
        print(f"    📊 検出エンコーディング: {encoding} (信頼度: {confidence:.2f})")
        
        # エンコーディングを修正してUTF-8で保存
        if encoding and encoding.lower() != 'utf-8':
            try:
                text = raw_data.decode(encoding)
            except:
                # 複数のエンコーディングを試す
                for enc in ['shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp', 'utf-8']:
                    try:
                        text = raw_data.decode(enc)
                        print(f"    ✅ {enc} で正常にデコード")
                        break
                    except:
                        continue
                else:
                    print(f"    ⚠️ デコードに失敗、元ファイルをそのまま使用")
                    shutil.copy2(srt_path, output_path)
                    return
        else:
            text = raw_data.decode('utf-8')
        
        # UTF-8で保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        print(f"    ✅ UTF-8で保存完了")
        
    except Exception as e:
        print(f"    ❌ エンコーディング修正エラー: {e}")
        # エラーの場合は元ファイルをコピー
        shutil.copy2(srt_path, output_path)

def add_subtitles_with_encoding_fix(video_dir="/input_videos", subtitle_dir="/input_subtitles", output_dir="/output"):
    """文字エンコーディング修正付きの字幕合成"""
    
    print("🎬 字幕合成（エンコーディング修正版）を開始")
    
    os.makedirs(output_dir, exist_ok=True)
    work_dir = "/tmp/subtitle_encoding_work"
    os.makedirs(work_dir, exist_ok=True)
    
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
    processed_count = 0
    
    print(f"\n📁 利用可能なファイル:")
    
    # 動画ファイル一覧
    video_files = []
    for filename in os.listdir(video_dir):
        if any(filename.lower().endswith(ext) for ext in video_extensions):
            video_files.append(filename)
            print(f"  📹 {filename}")
    
    # 字幕ファイル一覧
    subtitle_files = []
    for filename in os.listdir(subtitle_dir):
        if filename.endswith('.srt'):
            subtitle_files.append(filename)
            print(f"  📄 {filename}")
    
    for video_filename in video_files:
        base_name = os.path.splitext(video_filename)[0]
        subtitle_filename = f"{base_name}.srt"
        
        video_path = os.path.join(video_dir, video_filename)
        subtitle_path = os.path.join(subtitle_dir, subtitle_filename)
        
        if not os.path.exists(subtitle_path):
            print(f"⚠️ {video_filename} の字幕ファイルが見つかりません")
            continue
        
        try:
            print(f"\n🎬 処理中: {video_filename}")
            
            # 安全なファイル名を生成
            safe_base = "video_" + str(hash(base_name) % 10000).zfill(4)
            work_video = os.path.join(work_dir, f"{safe_base}.mp4")
            work_subtitle = os.path.join(work_dir, f"{safe_base}.srt")
            output_path = os.path.join(output_dir, f"{base_name}_字幕付き.mp4")
            
            print(f"  📄 字幕ファイル: {subtitle_filename}")
            
            # 動画ファイルをコピー
            print(f"  🔄 動画ファイルを作業ディレクトリにコピー...")
            shutil.copy2(video_path, work_video)
            
            # 字幕ファイルのエンコーディングを修正
            print(f"  🔄 字幕ファイルのエンコーディングを修正...")
            fix_subtitle_encoding(subtitle_path, work_subtitle)
            
            # 字幕ファイルの内容確認
            try:
                with open(work_subtitle, 'r', encoding='utf-8') as f:
                    sample = f.read(200)
                    print(f"  📝 字幕サンプル: {sample[:50]}...")
            except Exception as e:
                print(f"  ⚠️ 字幕ファイル読み込みエラー: {e}")
            
            # FFmpegで字幕合成
            print(f"  🔄 字幕を合成中...")
            
            # フォントファイルを指定（日本語対応）
            cmd = [
                'ffmpeg', '-y',
                '-i', work_video,
                '-vf', f"subtitles={work_subtitle}:force_style='FontName=DejaVu Sans,FontSize=20'",
                '-c:a', 'copy',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=work_dir)
            
            if result.returncode == 0 and os.path.exists(output_path):
                size = os.path.getsize(output_path)
                print(f"  ✅ 成功: {base_name}_字幕付き.mp4")
                print(f"  📊 ファイルサイズ: {size / (1024*1024):.1f} MB")
                processed_count += 1
            else:
                print(f"  ❌ FFmpeg失敗:")
                print(f"     stderr: {result.stderr}")
                
                # 代替方法: ass形式で試す
                print(f"  🔄 代替方法で再試行...")
                ass_path = work_subtitle.replace('.srt', '.ass')
                convert_srt_to_ass(work_subtitle, ass_path)
                
                cmd_alt = [
                    'ffmpeg', '-y',
                    '-i', work_video,
                    '-vf', f"ass={ass_path}",
                    '-c:a', 'copy',
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    output_path
                ]
                
                result_alt = subprocess.run(cmd_alt, capture_output=True, text=True, cwd=work_dir)
                
                if result_alt.returncode == 0:
                    print(f"  ✅ 代替方法で成功")
                    processed_count += 1
                else:
                    print(f"  ❌ 代替方法も失敗")
            
            # 作業ファイルをクリーンアップ
            for temp_file in [work_video, work_subtitle]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            print(f"  ❌ エラー ({video_filename}): {e}")
    
    print(f"\n🎉 処理完了: {processed_count}個の字幕付き動画を作成")

def convert_srt_to_ass(srt_path, ass_path):
    """SRTファイルをASS形式に変換（日本語フォント対応）"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # ASS形式のヘッダー
        ass_header = """[Script Info]
Title: Subtitle
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,20,&Hffffff,&Hffffff,&H0,&H0,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_header)
            
        print(f"    ✅ ASS形式に変換完了")
            
    except Exception as e:
        print(f"    ❌ ASS変換エラー: {e}")

if __name__ == "__main__":
    add_subtitles_with_encoding_fix()
