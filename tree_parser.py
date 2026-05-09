import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# AIに渡す際にノイズになる不要なフォルダを除外リストに設定
IGNORE_DIRS = {'.git', '__pycache__', '.vscode', 'node_modules', 'venv', '.idea'}

def generate_tree(dir_path, prefix=""):
    """再帰的にディレクトリ構造をテキスト化する関数"""
    tree_str = ""
    try:
        path_obj = Path(dir_path)
        if not path_obj.is_dir():
            return "指定されたパスはディレクトリではありません。\n"

        # フォルダとファイルを取得（アクセス権限がない場合はスキップ）
        try:
            contents = list(path_obj.iterdir())
        except PermissionError:
            return prefix + "└── [アクセス拒否]\n"

        # 除外フォルダをフィルタリングし、フォルダ→ファイルの順でソート
        contents = [c for c in contents if c.name not in IGNORE_DIRS]
        contents.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        
        pointers = ["├── "] * (len(contents) - 1) + ["└── "] if contents else []
        
        for pointer, item in zip(pointers, contents):
            tree_str += f"{prefix}{pointer}{item.name}\n"
            if item.is_dir():
                extension = "│   " if pointer == "├── " else "    "
                tree_str += generate_tree(item, prefix=prefix + extension)
                
        return tree_str
    except Exception as e:
        return f"エラーが発生しました: {e}\n"

class TreeParserApp:
    def __init__(self, root, initial_path=None):
        self.root = root
        self.root.title("ファイル構造解析ツール for AI")
        self.root.geometry("700x600")
        
        # UI構築
        self.setup_ui()
        
        # 初期パスのセットと実行
        if initial_path:
            self.path_var.set(initial_path)
            self.update_tree()

    def setup_ui(self):
        # 上部コントロールパネル
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="解析先パス:").pack(side=tk.LEFT)
        self.path_var = tk.StringVar()
        entry = ttk.Entry(top_frame, textvariable=self.path_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        # Enterキーで更新
        entry.bind("<Return>", lambda event: self.update_tree())

        ttk.Button(top_frame, text="参照...", command=self.select_dir).pack(side=tk.LEFT)

        # テキストエリア（スクロールバー付き）
        text_frame = ttk.Frame(self.root, padding=(10, 0, 10, 0))
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text_area = tk.Text(text_frame, wrap=tk.NONE, font=("Consolas", 10))
        
        vsb = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_area.yview)
        hsb = ttk.Scrollbar(text_frame, orient="horizontal", command=self.text_area.xview)
        self.text_area.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.text_area.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # 下部ボタンパネル
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="待機中...")
        ttk.Label(bottom_frame, textvariable=self.status_var, foreground="gray").pack(side=tk.LEFT)

        ttk.Button(bottom_frame, text="AI用にコピー", command=self.copy_to_clipboard).pack(side=tk.RIGHT)
        ttk.Button(bottom_frame, text="解析実行", command=self.update_tree).pack(side=tk.RIGHT, padx=5)

    def select_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.path_var.set(d)
            self.update_tree()

    def update_tree(self):
        target = self.path_var.get().strip()
        self.text_area.delete(1.0, tk.END)
        
        if not target or not os.path.exists(target):
            self.text_area.insert(tk.END, "有効なディレクトリパスを指定してください。")
            self.status_var.set("エラー: 無効なパス")
            return

        self.status_var.set("解析中...")
        self.root.update() # UIを更新
        
        # 構造を生成
        self.text_area.insert(tk.END, f"[{os.path.basename(target) or target}]\n")
        tree_text = generate_tree(target)
        self.text_area.insert(tk.END, tree_text)
        
        self.status_var.set("解析完了")

    def copy_to_clipboard(self):
        text_content = self.text_area.get(1.0, tk.END).strip()
        if text_content:
            self.root.clipboard_clear()
            self.root.clipboard_append(text_content)
            self.status_var.set("クリップボードにコピーしました！")
        else:
            self.status_var.set("コピーするテキストがありません。")

if __name__ == "__main__":
    # コマンドライン引数からパスを取得（例: python tree_parser.py C:\Users\xxx\Projects）
    target_dir = sys.argv[1] if len(sys.argv) > 1 else None
    
    root = tk.Tk()
    app = TreeParserApp(root, initial_path=target_dir)
    root.mainloop()