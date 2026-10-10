# -*- coding: utf-8 -*-
"""电子版 PDF 文字层提取（无需 OCR，无损、秒级）

用法：python extract_text.py <文件.pdf> [输出.txt]
输出默认写到 <文件名>_提取文本.txt，格式与 parse_questions.py 的输入约定一致：
每页以 `========== 第 N 页 ==========` 分隔。

依赖：pip install pymupdf
注意：仅适用于带文字层的电子版 PDF；扫描件请改用 ocr_pdf.py（OvisOCR2）。
"""
import sys
from pathlib import Path

import pymupdf


def main():
    if len(sys.argv) < 2:
        print("用法: python extract_text.py <文件.pdf> [输出.txt]")
        sys.exit(1)
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"文件不存在: {src}")
        sys.exit(1)
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name(src.stem + "_提取文本.txt")

    doc = pymupdf.open(src)
    parts = []
    empty_pages = 0
    for i, page in enumerate(doc):
        text = page.get_text()
        if not text.strip():
            empty_pages += 1
        parts.append(f"========== 第 {i + 1} 页 ==========")
        parts.append(text)
    dst.write_text("\n".join(parts), encoding="utf-8")

    total = len(doc)
    print(f"提取完成: {src.name} 共 {total} 页 → {dst.name}")
    if empty_pages == total:
        print("【警告】所有页面都没有文字层，可能是扫描件，请改用 ocr_pdf.py 做 OCR")
    elif empty_pages:
        print(f"【警告】有 {empty_pages} 页没有文字层（可能是插图页或扫描页）")


if __name__ == "__main__":
    main()
