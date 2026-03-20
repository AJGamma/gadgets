import argparse
import os
from pathlib import Path
from pypdf import PdfReader, PdfWriter

# ================= 固定的硬编码配置 =================
# 1. 原始小PDF所在的目录
SOURCE_DIR = "source_pdfs"
# 2. 合并后输出的PDF文件路径
MERGED_FILE = "merged.pdf"
# 3. 翻译完成后的合并PDF文件路径
TRANSLATED_MERGED_FILE = "translated_merged.pdf"
# 4. 拆分后输出文件的保存目录
OUTPUT_DIR = "output_pdfs"
# =================================================

def get_sorted_pdf_files(directory):
    """获取指定目录下所有PDF，并按文件名排序"""
    path = Path(directory)
    if not path.exists():
        print(f"错误: 目录 '{directory}' 不存在！")
        return[]
    
    pdfs = list(path.glob("*.pdf"))
    # 按文件名升序排列，确保 merge 和 split 顺序绝对一致
    pdfs.sort(key=lambda x: x.name)
    return pdfs

def merge_pdfs():
    """合并 PDF 文件"""
    pdfs = get_sorted_pdf_files(SOURCE_DIR)
    if not pdfs:
        print(f"在 '{SOURCE_DIR}' 中没有找到 PDF 文件。")
        return

    writer = PdfWriter()
    
    print("开始合并文件:")
    for pdf in pdfs:
        print(f" -> 正在添加: {pdf.name}")
        reader = PdfReader(pdf)
        for page in reader.pages:
            writer.add_page(page)
            
    with open(MERGED_FILE, "wb") as f:
        writer.write(f)
        
    print(f"\n合并完成！共合并了 {len(pdfs)} 个文件。")
    print(f"输出文件: {MERGED_FILE}")

def split_pdfs():
    """拆分翻译后的合并 PDF 文件"""
    # 确保输出目录存在
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    original_pdfs = get_sorted_pdf_files(SOURCE_DIR)
    if not original_pdfs:
        print(f"在 '{SOURCE_DIR}' 中没有找到原始 PDF 文件，无法计算拆分页数。")
        return
        
    if not Path(TRANSLATED_MERGED_FILE).exists():
        print(f"错误: 找不到翻译后的合并文件 '{TRANSLATED_MERGED_FILE}'！")
        return

    translated_reader = PdfReader(TRANSLATED_MERGED_FILE)
    total_translated_pages = len(translated_reader.pages)
    
    current_page_idx = 0
    
    print("开始拆分文件:")
    for orig_pdf in original_pdfs:
        orig_reader = PdfReader(orig_pdf)
        orig_page_count = len(orig_reader.pages)
        
        # 预防性检查：如果翻译后的页数不够分配了
        if current_page_idx + orig_page_count > total_translated_pages:
            print(f"\n警告: 翻译后的文档页数不足以拆分 '{orig_pdf.name}'！")
            print("可能是翻译过程中页码发生了增减。")
            
        writer = PdfWriter()
        
        # 计算当前文件应提取的结束页码
        end_page = min(current_page_idx + orig_page_count, total_translated_pages)
        
        # 提取对应页数
        for i in range(current_page_idx, end_page):
            writer.add_page(translated_reader.pages[i])
            
        # 拼接输出文件名 (zh_原文件名)
        output_filename = f"zh_{orig_pdf.name}"
        output_path = Path(OUTPUT_DIR) / output_filename
        
        with open(output_path, "wb") as f:
            writer.write(f)
            
        extracted_pages = end_page - current_page_idx
        print(f" -> 已生成: {output_filename} (提取了 {extracted_pages} 页)")
        
        current_page_idx += orig_page_count
        
    # 如果全部分配完后，翻译后文档还有多余的页面
    if current_page_idx < total_translated_pages:
        leftover_pages = total_translated_pages - current_page_idx
        print(f"\n警告: 翻译后的文件末尾多出了 {leftover_pages} 页，未分配给任何文件。")
        
    print(f"\n拆分完成！文件已保存至 '{OUTPUT_DIR}' 目录。")

def main():
    parser = argparse.ArgumentParser(description="按名称排序合并 PDF，或按原始页数拆分翻译后的 PDF。")
    parser.add_argument("action", choices=["merge", "split"], help="指定要执行的操作：'merge' 或 'split'")
    
    args = parser.parse_args()

    if args.action == "merge":
        merge_pdfs()
    elif args.action == "split":
        split_pdfs()

if __name__ == "__main__":
    main()
