# カスタムスタイル設定

# 基本スタイル設定
BASE_STYLES = {
    'default': {
        'font_name': 'Noto Sans CJK JP',
        'font_size': 24,
        'primary_color': '&H00FFFFFF',  # 白
        'outline_color': '&H00000000',  # 黒
        'outline_width': 2,
        'bold': 0,
        'italic': 0,
        'alignment': 2,  # 中央下
        'margin_v': 40
    }
}

# カスタムスタイルテンプレート
CUSTOM_STYLES = {
    # YouTube風スタイル
    'youtube': {
        'font_name': 'Arial Bold',
        'font_size': 32,
        'primary_color': '&H00FFFF00',  # 黄色
        'outline_color': '&H00000000',
        'outline_width': 3,
        'bold': 1,
        'alignment': 2,
        'margin_v': 50
    },
    
    # 映画風スタイル
    'cinema': {
        'font_name': 'Times New Roman',
        'font_size': 28,
        'primary_color': '&H00FFFFFF',
        'outline_color': '&H00000000',
        'outline_width': 1,
        'bold': 0,
        'italic': 1,
        'alignment': 2,
        'margin_v': 30
    },
    
    # アニメ風スタイル
    'anime': {
        'font_name': 'MS UI Gothic',
        'font_size': 26,
        'primary_color': '&H00FFFFFF',
        'outline_color': '&H000080FF',  # オレンジの縁取り
        'outline_width': 2,
        'bold': 1,
        'alignment': 8,  # 上部中央
        'margin_v': 30
    },
    
    # ニュース風スタイル
    'news': {
        'font_name': 'Arial',
        'font_size': 22,
        'primary_color': '&H00FFFFFF',
        'outline_color': '&H00000000',
        'outline_width': 1,
        'bold': 0,
        'alignment': 2,
        'margin_v': 20,
        'background': True,
        'background_color': '&H80000000'  # 半透明黒背景
    },
    
    # ゲーム実況風スタイル
    'gaming': {
        'font_name': 'Arial Black',
        'font_size': 30,
        'primary_color': '&H0000FF00',  # 緑
        'outline_color': '&H00000000',
        'outline_width': 4,
        'bold': 1,
        'alignment': 1,  # 左下
        'margin_v': 40
    }
}

# 色パレット
COLOR_PALETTE = {
    'white': '&H00FFFFFF',
    'black': '&H00000000',
    'red': '&H000000FF',
    'green': '&H0000FF00',
    'blue': '&H00FF0000',
    'yellow': '&H0000FFFF',
    'cyan': '&H00FFFF00',
    'magenta': '&H00FF00FF',
    'orange': '&H000080FF',
    'purple': '&H00800080',
    'pink': '&H00FF80FF',
    'lime': '&H0080FF00'
}

# フォントリスト
AVAILABLE_FONTS = [
    'Noto Sans CJK JP',
    'MS UI Gothic',
    'Arial',
    'Arial Black',
    'Times New Roman',
    'Helvetica',
    'DejaVu Sans',
    'Liberation Sans'
]
