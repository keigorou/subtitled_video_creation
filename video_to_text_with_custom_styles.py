import os
import sys
import argparse
import subprocess
import whisper

def parse_arguments():
    """引数解析"""
    parser = argparse.ArgumentParser(description='動画からカスタムスタイル字幕を生成')
    
    parser.add_argument('--input-dir', default='/input_videos')
    parser.add_argument('--output-dir', default='/output')
    parser.add_argument('--font', default='Noto Sans CJK JP')
    parser.add_argument('--size', type=int, default=48)
    parser.add_argument('--color', default='white')
    parser.add_argument('--outline-color', default='black')
    parser.add_argument('--outline-width', type=int, default=2)
    parser.add_argument('--position', default='bottom')
    parser.add_argument('--margin', type=int, default=40)
    parser.add_argument('--bold', action='store_true')
    parser.add_argument('--italic', action='store_true')
    parser.add_argument('--background', action='store_true')
    parser.add_argument('--format', choices=['ass', 'srt', 'both'], default='both')
    parser.add_argument('--preview', action='store_true')
    
    return parser.parse_args()

def main():
    """メイン処理"""
    
    args = parse_arguments()
    
    print("🎬 字幕生成（修正版）")
    print(f"📁 入力: {args.input_dir}")
    print(f"📁 出力: {args.output_dir}")
    print(f"📝 形式: {args.format}")
    
    # プレビューモード
    if args.preview:
        print("\n🔍 プレビューモード - 設定確認のみ")
        return
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Whisperモデル読み込み
    print("\n🤖 Whisperモデル読み込み中...")
    model = whisper.load_model("base")
    
    # 動画ファイル検索
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v']
    video_files = []
    
    for item in os.listdir(args.input_dir):
        if any(item.lower().endswith(ext) for ext in video_extensions):
            video_files.append(item)
            print(f"  📹 {item}")
    
    if not video_files:
        print("❌ 動画ファイルが見つかりません")
        return
    
    # 各動画ファイルを処理
    for filename in video_files:
        video_path = os.path.join(args.input_dir, filename)
        base_name = os.path.splitext(filename)[0]
        
        # ファイル名の安全化
        safe_base_name = "".join(c for c in base_name if c.isalnum() or c in ('-', '_'))[:50]
        
        print(f"\n🎬 処理中: {filename}")
        print(f"  📝 安全なベース名: {safe_base_name}")
        
        try:
            # 音声認識
            print("  🎤 音声認識実行中...")
            result = model.transcribe(
                video_path,
                language="ja",
                task="transcribe",
                verbose=False
            )
            
            print(f"  📊 認識された字幕数: {len(result['segments'])}")
            
            # SRTファイル作成を強制実行
            print(f"  📝 SRTファイル作成中...")
            srt_path = os.path.join(args.output_dir, f"{safe_base_name}_editable.srt")
            
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(result["segments"]):
                    start_time = seconds_to_srt_time(segment["start"])
                    end_time = seconds_to_srt_time(segment["end"])
                    text = segment["text"].strip()
                    
                    f.write(f"{i + 1}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
            
            srt_size = os.path.getsize(srt_path)
            print(f"  ✅ SRTファイル作成: {safe_base_name}_editable.srt ({srt_size} bytes)")
            
            # ASSファイル作成
            if args.format in ['ass', 'both']:
                print(f"  ✨ ASSファイル作成中...")
                ass_path = os.path.join(args.output_dir, f"{safe_base_name}_styled.ass")
                
                # シンプルなASSヘッダー
                ass_content = f"""[Script Info]
Title: {safe_base_name}
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{args.font},{args.size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,{1 if args.bold else 0},{1 if args.italic else 0},0,0,100,100,0,0,1,{args.outline_width},2,2,30,30,{args.margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
                
                for i, segment in enumerate(result["segments"]):
                    start_time = seconds_to_ass_time(segment["start"])
                    end_time = seconds_to_ass_time(segment["end"])
                    text = segment["text"].strip()
                    
                    dialogue_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}"
                    ass_content += dialogue_line + "\n"
                
                with open(ass_path, 'w', encoding='utf-8') as f:
                    f.write(ass_content)
                
                ass_size = os.path.getsize(ass_path)
                print(f"  ✅ ASSファイル作成: {safe_base_name}_styled.ass ({ass_size} bytes)")
            
            # テキストファイル作成
            txt_path = os.path.join(args.output_dir, f"{safe_base_name}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(result["text"])
            
            txt_size = os.path.getsize(txt_path)
            print(f"  ✅ テキストファイル作成: {safe_base_name}.txt ({txt_size} bytes)")
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            import traceback
            traceback.print_exc()

def seconds_to_srt_time(seconds):
    """秒をSRT時間形式に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def seconds_to_ass_time(seconds):
    """秒をASS時間形式に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

if __name__ == "__main__":
    main()
