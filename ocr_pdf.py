# -*- coding: utf-8 -*-
"""用 OvisOCR2 从 PDF 提取文本：每页渲染为图片 → 模型识别 → 输出 Markdown 文本"""
import sys
import time
from pathlib import Path

import pymupdf as fitz  # PyMuPDF（1.28+ 推荐 pymupdf 命名空间，fitz 为兼容旧名）
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration

MODEL_DIR = Path(__file__).parent / "models" / "OvisOCR2"
if len(sys.argv) < 2:
    print("用法: python ocr_pdf.py <扫描件.pdf> [输出.md]")
    sys.exit(1)
PDF_PATH = Path(sys.argv[1])
OUT_PATH = Path(sys.argv[2]) if len(sys.argv) > 2 else PDF_PATH.with_name(PDF_PATH.stem + "_OCR结果.md")

MIN_PIXELS = 448 * 448
MAX_PIXELS = 2880 * 2880   # 官方推荐值
RENDER_DPI = 200            # A4@200dpi ≈ 1654x2339 ≈ 3.9M 像素，在限制内
MAX_NEW_TOKENS = 8192

# 官方 README 中的标准提示词
PROMPT = (
    "\nExtract all readable content from the image in natural human reading order "
    "and output the result as a single Markdown document. For charts or images, "
    'represent them using an HTML image tag: <img src="images/bbox_{left}_{top}_{right}_{bottom}.jpg" />, '
    "where left, top, right, bottom are bounding box coordinates scaled to [0, 1000). "
    "Format formulas as LaTeX. Format tables as HTML: <table>...</table>. "
    "Transcribe all other text as standard Markdown. "
    "Preserve the original text without translation or paraphrasing."
)


def clean_truncated_repeats(text, min_text_len=8000, max_period=200, min_period=1,
                            min_repeat_chars=100, min_repeat_times=5):
    """官方 README 的后处理：清理截断导致的重复输出"""
    n = len(text)
    if n < min_text_len:
        return text
    max_period = min(max_period, n - 1)
    for unit_len in range(min_period, max_period + 1):
        if text[n - 1] != text[n - 1 - unit_len]:
            continue
        match_len = 1
        idx = n - 2
        while idx >= unit_len and text[idx] == text[idx - unit_len]:
            match_len += 1
            idx -= 1
        total_len = match_len + unit_len
        repeat_times = total_len // unit_len
        tail_len = total_len % unit_len
        if repeat_times >= min_repeat_times and total_len >= min_repeat_chars:
            return text[: n - total_len + unit_len] + text[n - tail_len:]
    return text


def pdf_to_images(pdf_path, dpi=RENDER_DPI):
    doc = fitz.open(pdf_path)
    images = []
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        images.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        print(f"[渲染] 第 {i + 1}/{len(doc)} 页: {pix.width}x{pix.height}", flush=True)
    doc.close()
    return images


def main():
    print(f"PyTorch: {torch.__version__}, CUDA 可用: {torch.cuda.is_available()}", flush=True)
    print(f"加载模型: {MODEL_DIR}", flush=True)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        str(MODEL_DIR), torch_dtype=torch.bfloat16, device_map="cuda"
    )
    model.eval()
    processor = AutoProcessor.from_pretrained(str(MODEL_DIR))
    print("模型加载完成", flush=True)

    messages = [{"role": "user", "content": [
        {"type": "image"}, {"type": "text", "text": PROMPT}]}]
    try:
        prompt_text = processor.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except (TypeError, KeyError):
        prompt_text = processor.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)

    images = pdf_to_images(PDF_PATH)
    print(f"共 {len(images)} 页，开始识别...", flush=True)

    results = []
    for i, image in enumerate(images):
        t0 = time.time()
        inputs = processor(
            text=[prompt_text], images=[image], return_tensors="pt",
            min_pixels=MIN_PIXELS, max_pixels=MAX_PIXELS,
        ).to(model.device)
        with torch.inference_mode():
            out_ids = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False)
        new_tokens = out_ids[:, inputs["input_ids"].shape[1]:]
        text = processor.batch_decode(new_tokens, skip_special_tokens=True)[0].strip()
        # 过滤视觉区域的 <img> 占位标签
        text = "\n\n".join(
            block for block in text.split("\n\n")
            if not block.strip().startswith('<img src="images/bbox_')
        )
        text = clean_truncated_repeats(text)
        results.append(f"\n\n<!-- ===== 第 {i + 1} 页 ===== -->\n\n{text}")
        print(f"[识别] 第 {i + 1}/{len(images)} 页完成，"
              f"耗时 {time.time() - t0:.1f}s，{len(text)} 字符", flush=True)

    OUT_PATH.write_text("".join(results).strip() + "\n", encoding="utf-8")
    print(f"\n完成！结果已保存到: {OUT_PATH}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
