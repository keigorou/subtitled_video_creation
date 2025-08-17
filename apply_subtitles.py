import os
import subprocess
import shutil
import glob
from pathlib import Path

def apply_subtitles_to_videos(video_dir="/input_videos", subtitle_dir="/input_subtitles", output_dir="/output"):
    """字幕を動画に自動合成"""
    
    print("🎬 字幕を動画に自動合成")
    print(f"📁 動画ディレクトリ: {video_dir}")
    print(f"📄 字幕ディレクトリ: {subtitle_dir}")
    print(f"📁 出力ディレクトリ: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    work_dir = "/tmp/subtitle_merge_work"
    os.makedirs(work_dir, exist_ok=True)
    
    # 利用可能なファイルを確認
    print(f"\n📁 利用可能な動画ファイル:")
    video_files = []
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
    
    for ext in video_extensions:
        files = glob.glob(os.path.join(video_dir, f"*{ext}"))
        files.extend(glob.glob(os.path.join(video_dir, f"*{ext.upper()}")))
        video_files.extend(files)
    
    if not video_files:
        print("❌ 動画ファイルが見つかりません")
        return
    
    for video_file in video_files:
        video_filename = os.path.basename(video_file)
        base_name = os.path.splitext(video_filename)[0]
        print(f"  - {video_filename}")
    
    print(f"\n📄 利用可能な字幕ファイル:")
    subtitle_files = []
    subtitle_extensions = ['.ass', '.srt']
    
    for ext in subtitle_extensions:
        files = glob.glob(os.path.join(subtitle_dir, f"*{ext}"))
        subtitle_files.extend(files)
    
    if not subtitle_files:
        print("❌ 字幕ファイルが見つかりません")
        return
    
    for subtitle_file in subtitle_files:
        subtitle_filename = os.path.basename(subtitle_file)
        print(f"  - {subtitle_filename}")
    
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
                subtitle_base = os.path.splitext(subtitle_filename)[0]
                
                print(f"\n🎬 処理中: {video_filename} + {subtitle_filename}")
                
                # 安全なファイル名を生成
                safe_name = f"merge_{hash(base_name + subtitle_base) % 10000:04d}"
                work_video = os.path.join(work_dir, f"{safe_name}.mp4")
                work_subtitle = os.path.join(work_dir, f"{safe_name}{Path(subtitle_file).suffix}")
                
                # 作業ディレクトリにコピー
                shutil.copy2(video_file, work_video)
                shutil.copy2(subtitle_file, work_subtitle)
                
                # 出力ファイル名を生成
                output_filename = f"{base_name}_{subtitle_base}_merged.mp4"
                output_path = os.path.join(output_dir, output_filename)
                
                # FFmpegコマンドを実行
                success = merge_subtitle_with_ffmpeg(work_video, work_subtitle, output_path)
                
                if success:
                    file_size = os.path.getsize(output_path)
                    print(f"  ✅ 成功: {output_filename}")
                    print(f"  📊 サイズ: {file_size / (1024*1024):.1f} MB")
                    processed_count += 1
                else:
                    print(f"  ❌ 失敗: {output_filename}")
                
                # 作業ファイルをクリーンアップ
                for temp_file in [work_video, work_subtitle]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        
        except Exception as e:
            print(f"  ❌ エラー ({video_filename}): {e}")
    
    print(f"\n🎉 処理完了: {processed_count}個の字幕付き動画を作成しました")

def find_matching_subtitles(video_base_name, subtitle_files):
    """動画ベース名に対応する字幕ファイルを検索"""
    matching = []
    
    for subtitle_file in subtitle_files:
        subtitle_filename = os.path.basename(subtitle_file)
        subtitle_base = os.path.splitext(subtitle_filename)[0]
        
        # 完全一致
        if subtitle_base == video_base_name:
            matching.append(subtitle_file)
        # 部分一致（_custom, _youtube等の接尾辞を考慮）
        elif subtitle_base.startswith(video_base_name + "_"):
            matching.append(subtitle_file)
        # 逆方向の一致も確認
        elif video_base_name.startswith(subtitle_base):
            matching.append(subtitle_file)
    
    return matching

def merge_subtitle_with_ffmpeg(video_path, subtitle_path, output_path):
    """FFmpegで字幕を動画に合成"""
    
    subtitle_ext = Path(subtitle_path).suffix.lower()
    
    try:
        if subtitle_ext == '.ass':
            # ASS形式の場合
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vf', f"ass={subtitle_path}",
                '-c:a', 'copy',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                output_path
            ]
        else:
            # SRT形式の場合
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
        print(f"  🔧 コマンド: ffmpeg -i {os.path.basename(video_path)} -vf {subtitle_ext[1:]}={os.path.basename(subtitle_path)} ...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(video_path))
        
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