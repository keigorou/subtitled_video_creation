import os
import sys
import argparse
import subprocess
import whisper
import jaconv
import mojimoji
import neologdn
import re

def parse_arguments():
    """引数解析"""
    parser = argparse.ArgumentParser(description='動画からカスタムスタイル字幕を生成（日本語最適化版）')
    
    parser.add_argument('--input-dir', default='/input_videos', help='入力動画ディレクトリ')
    parser.add_argument('--output-dir', default='/output', help='出力ディレクトリ')
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
    parser.add_argument('--model', default='base', choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'], 
                       help='Whisperモデルサイズ（日本語にはlarge-v3推奨）')
    parser.add_argument('--normalize', action='store_true', default=True,
                       help='日本語テキスト正規化を有効にする')
    
    return parser.parse_args()

def is_safe_character(char):
    """安全な文字かどうか判定（日本語対応）"""
    # ASCII英数字、ハイフン、アンダースコア
    if char.isalnum() or char in ('-', '_'):
        return True
    
    # 日本語文字範囲
    char_code = ord(char)
    
    # ひらがな (U+3040-U+309F)
    if 0x3040 <= char_code <= 0x309F:
        return True
    
    # カタカナ (U+30A0-U+30FF)
    if 0x30A0 <= char_code <= 0x30FF:
        return True
    
    # 漢字 (U+4E00-U+9FAF)
    if 0x4E00 <= char_code <= 0x9FAF:
        return True
    
    # 全角英数字 (U+FF00-U+FFEF)
    if 0xFF00 <= char_code <= 0xFFEF:
        return True
    
    return False

def normalize_japanese_text(text, enable_normalize=True):
    """日本語テキストの正規化処理"""
    if not enable_normalize:
        return text
    
    try:
        # 1. 基本的な正規化
        text = neologdn.normalize(text)
        
        # 2. 全角英数字を半角に変換（カナはそのまま）
        text = mojimoji.zen_to_han(text, kana=False)
        
        # 3. 不要な空白を削除
        text = text.strip()
        
        # 4. 連続する空白を単一の空白に
        text = re.sub(r'\s+', ' ', text)
        
        return text
    except Exception as e:
        print(f"  ⚠️ テキスト正規化エラー: {e}")
        return text

def main():
    """メイン処理"""
    
    args = parse_arguments()
    
    print("�� 字幕生成（日本語最適化版）")
    print(f"📁 入力: {args.input_dir}")
    print(f"📁 出力: {args.output_dir}")
    print(f"📄 形式: {args.format}")
    print(f"🤖 モデル: {args.model}")
    print(f"🔧 正規化: {'有効' if args.normalize else '無効'}")
    
    # プレビューモード
    if args.preview:
        print("\n📝 プレビューモード - 設定確認のみ")
        print("=" * 40)
        print(f"フォント: {args.font}")
        print(f"サイズ: {args.size}")
        print(f"色: {args.color}")
        print(f"太字: {'有効' if args.bold else '無効'}")
        print(f"斜体: {'有効' if args.italic else '無効'}")
        print(f"アウトライン: {args.outline_width}px")
        print(f"位置: {args.position}")
        print(f"マージン: {args.margin}px")
        return
    
    # 出力ディレクトリを作成
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 入力ディレクトリの存在確認
    if not os.path.exists(args.input_dir):
        print(f"❌ 入力ディレクトリが見つかりません: {args.input_dir}")
        return
    
    # Whisperモデル読み込み
    print(f"\n🤖 Whisperモデル読み込み中... ({args.model})")
    print("📝 日本語認識に最適化されたモデルを使用")
    
    try:
        model = whisper.load_model(args.model)
        print(f"✅ モデル読み込み完了: {args.model}")
    except Exception as e:
        print(f"❌ モデル読み込みエラー: {e}")
        print("📄 baseモデルにフォールバック")
        model = whisper.load_model("base")
    
    # 動画ファイル検索
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v']
    video_files = []
    
    print(f"\n📁 動画ファイル検索中: {args.input_dir}")
    for item in os.listdir(args.input_dir):
        if any(item.lower().endswith(ext) for ext in video_extensions):
            video_files.append(item)
            print(f"  📹 {item}")
    
    if not video_files:
        print("❌ 動画ファイルが見つかりません")
        print(f"📁 確認されたディレクトリ内容:")
        for item in os.listdir(args.input_dir):
            print(f"  - {item}")
        return
    
    print(f"\n📊 処理対象: {len(video_files)}個の動画ファイル")
    
    # 各動画ファイルを処理
    total_processed = 0
    for filename in video_files:
        video_path = os.path.join(args.input_dir, filename)
        base_name = os.path.splitext(filename)[0]
        
        # ファイル名の安全化（修正版）
        safe_base_name = "".join(c for c in base_name if is_safe_character(c))[:50]
        if not safe_base_name:  # 全て除外された場合のフォールバック
            safe_base_name = f"video_{hash(base_name) % 10000:04d}"
        
        print(f"\n🎬 処理中: {filename}")
        print(f"  📝 安全なベース名: {safe_base_name}")
        
        try:
            # 音声認識（日本語最適化設定）
            print("  🎤 音声認識実行中（日本語最適化）...")
            result = model.transcribe(
                video_path,
                language="ja",
                task="transcribe",
                verbose=False,
                word_timestamps=True,
                # 日本語に最適化された設定
                temperature=0.0,
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6
            )
            
            print(f"  📊 認識された字幕数: {len(result['segments'])}")
            
            # テキストの正規化処理
            if args.normalize:
                print("  🔧 日本語テキスト正規化中...")
                for segment in result["segments"]:
                    original_text = segment["text"]
                    normalized_text = normalize_japanese_text(original_text, args.normalize)
                    segment["text"] = normalized_text
                    
                    if original_text != normalized_text:
                        print(f"    📝 正規化: '{original_text}' -> '{normalized_text}'")
            
            # SRTファイル作成を強制実行
            print(f"  📄 SRTファイル作成中...")
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
                
                # 日本語に最適化されたASSヘッダー
                ass_content = f"""[Script Info]
Title: {safe_base_name}
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

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
                # 正規化されたテキストを使用
                full_text = " ".join([segment["text"] for segment in result["segments"]])
                f.write(full_text)
            
            txt_size = os.path.getsize(txt_path)
            print(f"  ✅ テキストファイル作成: {safe_base_name}.txt ({txt_size} bytes)")
            
            total_processed += 1
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 処理完了: {total_processed}/{len(video_files)} ファイル")
    
    # 最終結果確認
    print(f"\n📁 生成されたファイル一覧:")
    for item in os.listdir(args.output_dir):
        item_path = os.path.join(args.output_dir, item)
        size = os.path.getsize(item_path)
        print(f"  📄 {item} ({size} bytes)")

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
