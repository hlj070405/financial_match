import os
import time

# 设置国内 Hugging Face 镜像源，解决下载模型超时问题
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from docling.document_converter import DocumentConverter

def test_docling(pdf_path: str):
    print(f"Testing Docling on: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return
        
    start_time = time.time()
    
    # Initialize converter
    converter = DocumentConverter()
    
    print("Converting document...")
    # Convert PDF
    result = converter.convert(pdf_path)
    
    # Export to Markdown
    md_content = result.document.export_to_markdown()
    
    end_time = time.time()
    
    print(f"\nConversion completed in {end_time - start_time:.2f} seconds")
    print(f"Generated Markdown length: {len(md_content)} chars")
    
    # Save output to same directory
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    out_dir = os.path.dirname(pdf_path)
    out_path = os.path.join(out_dir, f"{base_name}_docling.md")
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"Saved to: {out_path}")
    
    # Show a snippet
    print("\n--- Snippet (first 1000 chars) ---")
    print(md_content[:1000])
    print("----------------------------------\n")

if __name__ == "__main__":
    # Test on one of the smaller reports first
    test_pdf = r"c:\Users\Administrator\Desktop\大数据 主题赛\pdf-rag-system\backend\financial_reports\000001_平安银行_2025Q3_report.pdf"
    test_docling(test_pdf)
