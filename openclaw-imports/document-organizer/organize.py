#!/usr/bin/env python3
"""
Document Organizer - Organize files by analyzing content
Supports: PDF, Word, Excel, and more
"""

import os
import sys
import shutil
import pandas as pd
import docx
from pathlib import Path

# 默认分类规则
DEFAULT_CATEGORIES = {
    "工作": ["报告", "方案", "计划", "总结", "周报", "日报", "会议", "纪要", "通知"],
    "财务": ["账单", "发票", "报表", "财务", "预算", "支出", "收入", "合同", "报价"],
    "技术": ["代码", "API", "技术", "文档", "开发", "手册", "教程", "说明书"],
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "视频": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv"],
    "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "PDF文档": [".pdf"],
    "表格": [".xlsx", ".xls", ".csv"],
    "文档": [".docx", ".doc", ".txt", ".md", ".rtf"],
    "其他": []
}

def read_pdf(filepath):
    """Read PDF file content"""
    try:
        import pypdf
        reader = pypdf.PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text[:2000]  # Limit to 2000 chars
    except Exception as e:
        return f"[PDF读取失败: {e}]"

def read_word(filepath):
    """Read Word document content"""
    try:
        doc = docx.Document(filepath)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text[:2000]
    except Exception as e:
        return f"[Word读取失败: {e}]"

def read_excel(filepath):
    """Read Excel file and return summary"""
    try:
        df = pd.read_excel(filepath)
        return f"[Excel: {len(df)}行 x {len(df.columns)}列, 列名: {list(df.columns[:5])}]"
    except Exception as e:
        return f"[Excel读取失败: {e}]"

def analyze_content(filepath, text_content):
    """Analyze file content and determine category"""
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    
    # First check by extension
    for category, extensions in DEFAULT_CATEGORIES.items():
        if ext in extensions and category not in ["工作", "财务", "技术"]:
            return category
    
    # Then check by keywords in filename
    for category, keywords in DEFAULT_CATEGORIES.items():
        if category in ["工作", "财务", "技术"]:
            for keyword in keywords:
                if keyword in filename or keyword in str(text_content):
                    return category
    
    return "其他"

def organize_folder(folder_path, create_subfolders=True, read_contents=True):
    """Organize files in a folder"""
    if not os.path.exists(folder_path):
        print(f"❌ 文件夹不存在: {folder_path}")
        return
    
    print(f"\n📁 开始整理文件夹: {folder_path}")
    print("=" * 60)
    
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    total_files = len(files)
    
    # Create category folders
    categories_created = {}
    
    # Analyze each file
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        ext = os.path.splitext(filename)[1].lower()
        
        print(f"\n📄 处理: {filename}")
        
        # Read content
        text_content = ""
        if ext == ".pdf":
            text_content = read_pdf(filepath)
        elif ext in [".docx", ".doc"]:
            text_content = read_word(filepath)
        elif ext in [".xlsx", ".xls", ".csv"]:
            text_content = read_excel(filepath)
        elif ext in [".txt", ".md"]:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text_content = f.read(2000)
            except:
                pass
        
        # Analyze and categorize
        category = analyze_content(filepath, text_content)
        
        print(f"   分类: {category}")
        
        # Move file if different category
        if create_subfolders and category != "当前目录":
            dest_folder = os.path.join(folder_path, category)
            os.makedirs(dest_folder, exist_ok=True)
            dest_path = os.path.join(dest_folder, filename)
            
            if os.path.exists(dest_path):
                # Handle duplicate filename
                base, ext = os.path.splitext(filename)
                dest_path = os.path.join(dest_folder, f"{base}_副本{ext}")
            
            shutil.move(filepath, dest_path)
            print(f"   → 已移动到: {category}/")
            categories_created[category] = categories_created.get(category, 0) + 1
        else:
            print(f"   → 保留在原位置")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 整理完成！")
    print(f"   总文件数: {total_files}")
    print(f"   创建分类文件夹: {len(categories_created)}")
    for cat, count in categories_created.items():
        print(f"   - {cat}: {count}个文件")

def main():
    if len(sys.argv) < 2:
        print("📁 Document Organizer - 文档整理工具")
        print("\n用法:")
        print("  python3 organize.py <文件夹路径>    # 整理文件夹")
        print("  python3 organize.py --help         # 显示帮助")
        print("\n示例:")
        print("  python3 organize.py /media/usb")
        print("  python3 organize.py ~/Documents")
        return
    
    folder_path = sys.argv[1]
    organize_folder(folder_path)

if __name__ == "__main__":
    main()
