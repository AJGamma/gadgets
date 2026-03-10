import os
import sys
import json
import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

# 定义默认输出目录
OUTPUT_DIR = os.path.join(os.getcwd(), 'out')

class PDFToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 长图拼接/拆分工具")
        self.root.geometry("500x400")
        
        # 确保输出目录存在
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        self.file_path = None
        self.json_path = None

        self._init_ui()

    def _init_ui(self):
        # 1. 拖拽区域
        self.drop_frame = tk.LabelFrame(self.root, text="操作区域", padx=10, pady=10)
        self.drop_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.lbl_instruction = tk.Label(
            self.drop_frame, 
            text="👉 将 PDF 文件拖拽到这里\n或者点击下方按钮选择文件",
            font=("Arial", 12),
            fg="#555",
            bg="#f0f0f0",
            relief="sunken",
            width=40,
            height=8
        )
        self.lbl_instruction.pack(pady=10, fill="x")

        # 注册拖拽事件
        self.lbl_instruction.drop_target_register(DND_FILES)
        self.lbl_instruction.dnd_bind('<<Drop>>', self.drop_file)

        # 2. 文件信息显示
        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack(fill="x", padx=10)
        
        self.lbl_selected = tk.Label(self.info_frame, text="未选择文件", fg="blue", wraplength=480)
        self.lbl_selected.pack(pady=5)

        # 3. 按钮区域
        self.btn_frame = tk.Frame(self.root, pady=10)
        self.btn_frame.pack(fill="x")

        self.btn_browse = tk.Button(self.btn_frame, text="选择文件", command=self.browse_file)
        self.btn_browse.pack(side="left", padx=20)

        # 默认禁用操作按钮，直到文件被加载
        self.btn_action = tk.Button(self.btn_frame, text="开始处理", state="disabled", command=self.run_process, bg="#dddddd")
        self.btn_action.pack(side="right", padx=20)

        # 4. 日志区域
        self.log_text = tk.Text(self.root, height=6, state="disabled", bg="#f4f4f4", font=("Consolas", 9))
        self.log_text.pack(fill="x", side="bottom", padx=10, pady=5)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.root.update()

    def drop_file(self, event):
        # 处理拖拽进来的路径（去除可能的花括号）
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        self.load_file(file_path)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.load_file(file_path)

    def load_file(self, path):
        if not path.lower().endswith('.pdf'):
            messagebox.showerror("错误", "请选择 PDF 文件")
            return

        self.file_path = path
        self.lbl_selected.config(text=f"当前文件: {os.path.basename(path)}")
        
        # 智能判断模式
        try:
            doc = fitz.open(path)
            page_count = doc.page_count
            doc.close()

            # 自动推测配置文件路径 (假设在同一目录下，或者在 out 目录下)
            # 策略：如果输入是 xxx.pdf，寻找 xxx.json 或 out/xxx.json
            base_name = os.path.splitext(os.path.basename(path))[0]
            possible_json_1 = os.path.join(os.path.dirname(path), f"{base_name}.json")
            possible_json_2 = os.path.join(OUTPUT_DIR, f"{base_name}.json")
            
            # 如果文件名包含 _merged，尝试去掉后缀寻找原始json
            # 例如: input_merged.pdf -> input.json
            possible_json_3 = None
            if "_merged" in base_name:
                original_name = base_name.replace("_merged", "")
                possible_json_3 = os.path.join(OUTPUT_DIR, f"{original_name}.json")

            if page_count > 1:
                self.mode = "merge"
                self.btn_action.config(text="执行合并 (Merge)", state="normal", bg="#d0f0c0")
                self.log(f"检测到多页 PDF ({page_count}页)。准备合并。")
            else:
                self.mode = "split"
                self.btn_action.config(text="执行拆分 (Split)", state="normal", bg="#ffd0d0")
                
                # 尝试自动定位 JSON
                if os.path.exists(possible_json_1):
                    self.json_path = possible_json_1
                elif os.path.exists(possible_json_2):
                    self.json_path = possible_json_2
                elif possible_json_3 and os.path.exists(possible_json_3):
                    self.json_path = possible_json_3
                else:
                    self.json_path = None
                
                if self.json_path:
                    self.log(f"检测到单页 PDF。已自动关联配置文件: {os.path.basename(self.json_path)}")
                else:
                    self.log(f"检测到单页 PDF。警告：未找到同名 JSON 配置文件，点击执行时需手动选择。")

        except Exception as e:
            self.log(f"读取文件出错: {e}")

    def run_process(self):
        if self.mode == "merge":
            self.process_merge()
        elif self.mode == "split":
            self.process_split()

    def process_merge(self):
        try:
            self.log("正在合并...")
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            
            # 自动生成输出路径
            output_pdf = os.path.join(OUTPUT_DIR, f"{base_name}_merged.pdf")
            output_json = os.path.join(OUTPUT_DIR, f"{base_name}_merged.json")

            doc = fitz.open(self.file_path)
            total_height = 0
            max_width = 0
            page_heights = []

            for page in doc:
                rect = page.rect
                total_height += rect.height
                if rect.width > max_width: max_width = rect.width
                page_heights.append(rect.height)

            out_doc = fitz.open()
            big_page = out_doc.new_page(width=max_width, height=total_height)
            
            current_y = 0
            for i, page in enumerate(doc):
                rect = page.rect
                target_rect = fitz.Rect(0, current_y, rect.width, current_y + rect.height)
                big_page.show_pdf_page(target_rect, doc, i)
                current_y += rect.height

            out_doc.save(output_pdf)
            
            # 保存配置文件
            config_data = {
                "original_filename": base_name,
                "max_width": max_width,
                "page_heights": page_heights
            }
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)

            self.log(f"✅ 合并成功！")
            self.log(f"文件已保存至: {output_pdf}")
            self.log(f"配置已保存至: {output_json}")
            
            # 自动将新生成的 JSON 路径关联到当前 session，方便用户立即测试拆分（虽然不太常见）
            self.json_path = output_json
            
            doc.close()
            out_doc.close()
            messagebox.showinfo("成功", f"文件已保存到 ./out 目录")

        except Exception as e:
            self.log(f"❌ 错误: {e}")
            messagebox.showerror("错误", str(e))

    def process_split(self):
        # 如果之前没自动找到 JSON，现在让用户选
        if not self.json_path:
            self.json_path = filedialog.askopenfilename(
                title="请选择对应的 JSON 布局配置文件",
                filetypes=[("JSON Config", "*.json")],
                initialdir=OUTPUT_DIR
            )
            if not self.json_path:
                self.log("取消操作：未选择配置文件。")
                return

        try:
            self.log(f"正在拆分... 使用配置: {os.path.basename(self.json_path)}")
            
            with open(self.json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            page_heights = config["page_heights"]
            
            src_doc = fitz.open(self.file_path)
            src_page = src_doc[0]
            out_doc = fitz.open()
            
            current_y = 0
            for height in page_heights:
                # 使用原宽度 (src_page.rect.width) 以防编辑后宽度微调，或者使用 config['max_width']
                # 这里使用 PDF 实际宽度更安全
                new_page = out_doc.new_page(width=src_page.rect.width, height=height)
                clip_rect = fitz.Rect(0, current_y, src_page.rect.width, current_y + height)
                new_page.show_pdf_page(new_page.rect, src_doc, 0, clip=clip_rect)
                current_y += height

            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            # 去除 _merged 后缀以避免文件名越来越长
            clean_name = base_name.replace("_merged", "")
            output_pdf = os.path.join(OUTPUT_DIR, f"{clean_name}_split.pdf")
            
            out_doc.save(output_pdf)
            self.log(f"✅ 拆分成功！")
            self.log(f"文件已保存至: {output_pdf}")
            
            src_doc.close()
            out_doc.close()
            messagebox.showinfo("成功", f"文件已拆分并保存到 ./out 目录")

        except Exception as e:
            self.log(f"❌ 错误: {e}")
            messagebox.showerror("错误", str(e))

if __name__ == "__main__":
    # 初始化 TkinterDnD
    root = TkinterDnD.Tk()
    app = PDFToolApp(root)
    root.mainloop()
