import os
import subprocess
import shutil

def add_html_subtitles(video_dir="/input_videos", subtitle_dir="/input_subtitles", output_dir="/output"):
    """HTMLマーカー字幕を動画に合成"""
    
    print("🎬 HTMLマーカー字幕を動画に合成")
    
    os.makedirs(output_dir, exist_ok=True)
    work_dir = "/tmp/html_subtitle_work"
    os.makedirs(work_dir, exist_ok=True)
    
    processed_count = 0
    
    for video_filename in os.listdir(video_dir):
        if video_filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
            base_name = os.path.splitext(video_filename)[0]
            html_subtitle_filename = f"{base_name}_html.srt"
            
            video_path = os.path.join(video_dir, video_filename)
            subtitle_path = os.path.join(subtitle_dir, html_subtitle_filename)
            
            if not os.path.exists(subtitle_path):
                print(f"⚠️ {video_filename} のHTMLマーカー字幕が見つかりません")
                continue
            
            try:
                print(f"\n🎬 処理中: {video_filename}")
                
                # 安全なファイル名を生成
                safe_name = f"video_{hash(base_name) % 10000:04d}"
                work_video = os.path.join(work_dir, f"{safe_name}.mp4")
                work_subtitle = os.path.join(work_dir, f"{safe_name}.srt")
                
                # ファイルをコピー
                shutil.copy2(video_path, work_video)
                shutil.copy2(subtitle_path, work_subtitle)
                
                # 出力ファイル名
                output_path = os.path.join(output_dir, f"{base_name}_html_subtitled.mp4")
                
                # FFmpegコマンド実行
                cmd = [
                    'ffmpeg', '-y',
                    '-i', work_video,
                    '-vf', f"subtitles={work_subtitle}",
                    '-c:a', 'copy',
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23',
                    output_path
                ]
                
                print(f"  🔄 HTMLマーカー字幕を合成中...")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=work_dir)
                
                if result.returncode == 0:
                    size = os.path.getsize(output_path)
                    print(f"  ✅ 成功: {base_name}_html_subtitled.mp4")
                    print(f"  📊 サイズ: {size / (1024*1024):.1f} MB")
                    processed_count += 1
                else:
                    print(f"  ❌ エラー: {result.stderr}")
                
                # クリーンアップ
                for temp_file in [work_video, work_subtitle]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        
            except Exception as e:
                print(f"  ❌ エラー: {e}")
    
    print(f"\n🎉 {processed_count}個のHTMLマーカー字幕付き動画を作成")

if __name__ == "__main__":
    add_html_subtitles()
