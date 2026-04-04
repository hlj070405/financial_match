import os
import time
import argparse
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List

import pymupdf4llm

def convert_single_pdf(pdf_path: str) -> bool:
    """转换单个 PDF 为 Markdown"""
    try:
        print(f"[{os.getpid()}] 开始处理: {os.path.basename(pdf_path)}")
        start_time = time.time()

        md_content = pymupdf4llm.to_markdown(pdf_path)

        # 将生成的 md 保存到同一目录下
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        out_dir = os.path.dirname(pdf_path)
        out_path = os.path.join(out_dir, f"{base_name}.md")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        elapsed = time.time() - start_time
        print(f"[{os.getpid()}] ✅ 完成: {os.path.basename(pdf_path)} (耗时: {elapsed:.2f}s, 大小: {len(md_content)} 字符)")
        return True
    except Exception as e:
        print(f"[{os.getpid()}] ❌ 失败: {os.path.basename(pdf_path)}")
        traceback.print_exc()
        return False

def batch_convert(source_dir: str, workers: int = 2):
    """批量转换目录下的所有 PDF"""
    if not os.path.exists(source_dir):
        print(f"目录不存在: {source_dir}")
        return
        
    pdf_files = list(Path(source_dir).rglob("*.pdf"))
    if not pdf_files:
        print(f"在 {source_dir} 中未找到 PDF 文件")
        return
        
    print(f"共找到 {len(pdf_files)} 个 PDF 文件，准备开始转换 (线程数: {workers})")
    
    success_count = 0
    start_total = time.time()
    
    # 过滤出还没转换过的文件
    pending_files = []
    for pdf_path in pdf_files:
        md_path = pdf_path.with_suffix(".md")
        if not md_path.exists():
            pending_files.append(str(pdf_path))
        else:
            print(f"⏭️ 跳过已存在: {md_path.name}")
            
    if not pending_files:
        print("所有文件均已转换完成！")
        return
        
    print(f"需要转换 {len(pending_files)} 个文件。")
    
    if workers <= 1:
        print("使用单进程模式顺序转换...")
        results = [convert_single_pdf(p) for p in pending_files]
    else:
        print(f"使用多进程模式 (workers={workers})...")
        with ProcessPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(convert_single_pdf, pending_files))
        
    success_count = sum(1 for r in results if r)
    elapsed_total = time.time() - start_total
    
    print(f"\n批量转换完成！")
    print(f"成功: {success_count}/{len(pending_files)}")
    print(f"总耗时: {elapsed_total:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量将 PDF 转换为 Markdown")
    parser.add_argument("--dir", type=str, default="../financial_reports", help="PDF 文件所在目录")
    parser.add_argument("--workers", type=int, default=2, help="并发工作进程数")
    
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, "financial_reports")
    if args.dir != "../financial_reports":
        target_dir = args.dir
        
    batch_convert(target_dir, args.workers)
