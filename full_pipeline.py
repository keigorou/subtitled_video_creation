import os
import subprocess
import sys
import shlex

def full_subtitle_pipeline(style_args=""):
    """動画→字幕生成→合成の全自動パイプライン"""
    
    print("🚀 全自動字幕パイプライン開始")
    print("=" * 50)
    
    # Phase 1: 動画から字幕生成
    print("\n📍 Phase 1: 動画から字幕を生成")
    
    cmd = ["python", "video_to_text_with_custom_styles.py"]
    
    # 引数が文字列の場合は適切に分割
    if isinstance(style_args, str) and style_args:
        try:
            # shlex.split を使ってクォートを考慮して分割
            parsed_args = shlex.split(style_args)
            cmd.extend(parsed_args)
        except ValueError as e:
            print(f"⚠️ 引数解析エラー: {e}")
            print(f"元の引数: {style_args}")
            # フォールバック: 単純分割
            cmd.extend(style_args.split())
    elif isinstance(style_args, list):
        cmd.extend(style_args)
    
    print(f"🔧 実行コマンド: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Phase 1 失敗")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    print("✅ Phase 1 完了: 字幕ファイル生成")
    if result.stdout:
        print("Phase 1 出力:")
        print(result.stdout)
    
    # Phase 2: 字幕を動画に合成
    print("\n📍 Phase 2: 字幕を動画に合成")
    
    result = subprocess.run(["python", "apply_subtitles.py"], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Phase 2 失敗")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    print("✅ Phase 2 完了: 字幕付き動画生成")
    if result.stdout:
        print("Phase 2 出力:")
        print(result.stdout)
    
    print("\n🎉 全パイプライン完了!")
    
    return True

if __name__ == "__main__":
    # コマンドライン引数をスタイル設定として使用
    if len(sys.argv) > 1:
        # sys.argv[1:]をそのままリストとして渡す
        style_args = sys.argv[1:]
        print(f"🎨 スタイル設定: {' '.join(style_args)}")
    else:
        style_args = []
    
    success = full_subtitle_pipeline(style_args)
    
    if success:
        print("\n📁 出力ファイルを確認してください:")
        print("  - 字幕ファイル: ./output/")
        print("  - 字幕付き動画: ./merged_videos/")
    else:
        print("\n❌ パイプライン処理に失敗しました")
