import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# AIに渡す際にノイズになる不要なフォルダ・ファイルを除外
IGNORE_DIRS = {'.git', '__pycache__', '.vscode', 'node_modules', 'venv', '.idea', '.next', 'dist', 'build'}
IGNORE_FILES = {'.DS_Store', 'Thumbs.db', 'package-lock.json', 'yarn.lock'}

def generate_tree(dir_path, prefix=""):
    """再帰的にディレクトリ構造をテキスト化する関数"""
    tree_str = ""
    try:
        path_obj = Path(dir_path)
        if not path_obj.is_dir():
            return ""

        contents = [c for c in path_obj.iterdir() if c.name not in IGNORE_DIRS and c.name not in IGNORE_FILES]
        contents.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        
        pointers = ["├── "] * (len(contents) - 1) + ["└── "] if contents else []
        
        for pointer, item in zip(pointers, contents):
            tree_str += f"{prefix}{pointer}{item.name}\n"
            if item.is_dir():
                extension = "│   " if pointer == "├── " else "    "
                tree_str += generate_tree(item, prefix=prefix + extension)
        return tree_str
    except Exception as e:
        return f"{prefix}└── [Error: {e}]\n"

def generate_full_contents(dir_path):
    """ディレクトリ内の全ファイルの内容をAI向けフォーマットで書き出す関数"""
    output = ""
    path_obj = Path(dir_path)
    
    for root, dirs, files in os.walk(dir_path):
        # 除外ディレクトリをスキップ
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
                
            file_path = Path(root) / file
            rel_path = file_path.relative_to(path_obj)
            
            output += f"\n{'='*50}\n"
            output += f"FILE: {rel_path}\n"
            output += f"{'='*50}\n"
            
            try:
                # テキストとして読み込み（バイナリ等はエラーが出るので無視）
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    output += content + "\n"
            except (UnicodeDecodeError, PermissionError):
                output += "[Skipped: Binary file or encoding not supported]\n"
            except Exception as e:
                output += f"[Error reading file: {e}]\n"
                
    return output

class TreeParserApp:
    def __init__(self, root, initial_path=None):
        self.root = root
        self.root.title("AI用コード解析ツール (Structure & Contents)")
        self.root.geometry("800x700")
        
        # 変数
        self.path_var = tk.StringVar()
        self.include_contents_var = tk.BooleanVar(value=False) # デフォルトは構造のみ
        
        self.setup_ui()
        
        if initial_path:
            self.path_var.set(initial_path)
            self.update_tree()

    def setup_ui(self):
        # 上部：パス入力エリア
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="解析パス:").pack(side=tk.LEFT)
        entry = ttk.Entry(top_frame, textvariable=self.path_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        entry.bind("<Return>", lambda e: self.update_tree())
        ttk.Button(top_frame, text="参照", command=self.select_dir).pack(side=tk.LEFT)

        # 中部：オプション設定
        option_frame = ttk.Frame(self.root, padding=(10, 0))
        option_frame.pack(fill=tk.X)
        
        ttk.Checkbutton(
            option_frame, 
            text="ファイルの内容も出力に含める (AIのコンテキスト用)", 
            variable=self.include_contents_var,
            command=self.update_tree # 切り替え時に自動更新
        ).pack(side=tk.LEFT)

        # 中央：テキスト表示エリア
        text_frame = ttk.Frame(self.root, padding=10)
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

        # 下部：ステータスとボタン
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="待機中...")
        ttk.Label(bottom_frame, textvariable=self.status_var, foreground="gray").pack(side=tk.LEFT)

        ttk.Button(bottom_frame, text="コピーして完了", command=self.copy_to_clipboard).pack(side=tk.RIGHT)
        ttk.Button(bottom_frame, text="解析実行", command=self.update_tree).pack(side=tk.RIGHT, padx=5)

    def select_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.path_var.set(d)
            self.update_tree()

    def update_tree(self):
        target = self.path_var.get().strip()
        if not target or not os.path.exists(target):
            return

        self.status_var.set("解析中...")
        self.root.update()
        
        self.text_area.delete(1.0, tk.END)
        
        # 1. ディレクトリ構造の生成
        output = f"DIRECTORY STRUCTURE:\n[{os.path.basename(target) or target}]\n"
        output += generate_tree(target)
        
        # 2. 内容を含める場合
        if self.include_contents_var.get():
            output += "\n\n" + "="*50 + "\n"
            output += "FILE CONTENTS LIST\n"
            output += "="*50 + "\n"
            output += generate_full_contents(target)
        
        self.text_area.insert(tk.END, output)
        self.status_var.set("解析完了")

    def copy_to_clipboard(self):
        text_content = self.text_area.get(1.0, tk.END).strip()
        if text_content:
            self.root.clipboard_clear()
            self.root.clipboard_append(text_content)
            self.status_var.set("クリップボードにコピーしました！")
        else:
            self.status_var.set("コピーする内容がありません。")

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else None
    root = tk.Tk()
    app = TreeParserApp(root, initial_path=target_dir)
    root.mainloop()