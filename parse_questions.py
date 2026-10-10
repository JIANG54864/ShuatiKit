# -*- coding: utf-8 -*-
"""把提取的 PDF 文本解析为结构化题库 JSON

用法：python parse_questions.py <提取文本.txt>
输出：questions.json + 题库预览.md + shuati-miniprogram/data/questions.js

文本格式约定：
  章节标题：「第一部分」/「第一节」/「课后练习」行（标题为其后首个非空行）
  题目起始：1.（单选）题干……
  选项：A. xxx（四个选项，可同行或分行）
  答案：【答案】D 解析文字（解析可省略）
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT_JSON = ROOT / "questions.json"
OUT_PREVIEW = ROOT / "题库预览.md"
OUT_JS = ROOT / "shuati-miniprogram" / "data" / "questions.js"

PAGE_SEP = re.compile(r"^=+ 第 \d+ 页 =+$")
# 页眉：第X页共117页，含 OCR 变体（数字 1 被识别为字母 l / I）
PAGE_HEADER = re.compile(r"^第[0-9lI]{1,4}页共[0-9lI]{1,4}页$")
PART_MARK = re.compile(r"^第[一二三四五六七八九十]+部分$")
SECTION_MARK = re.compile(r"^第[一二三四五六七八九十]+节$")
Q_START = re.compile(r"^(\d+)\s*[.．]\s*（单选）")
PRACTICE_MARK = re.compile(r"^课后练习$")


def clean_text(s: str) -> str:
    """合并折行、规范空格：仅保留 ASCII 字母数字之间的空格"""
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"(?<![A-Za-z0-9])\s+", "", s)
    s = re.sub(r"\s+(?![A-Za-z0-9])", "", s)
    return s.strip()


def main():
    if len(sys.argv) < 2:
        print("用法: python parse_questions.py <提取文本.txt>（电子版 PDF 可先用 extract_text.py 提取）")
        sys.exit(1)
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"文件不存在: {src}")
        sys.exit(1)
    name = src.stem.replace("_提取文本", "")
    raw_lines = src.read_text(encoding="utf-8").split("\n")

    # 第一遍：剔除分页标记和页眉，同时记录每行所属页码
    lines, pages = [], []
    cur_page = 0
    for ln in raw_lines:
        s = ln.strip()
        m = re.match(r"^=+ 第 (\d+) 页 =+$", s)
        if m:
            cur_page = int(m.group(1))
            continue
        if PAGE_HEADER.match(s):
            continue
        lines.append(s)
        pages.append(cur_page)

    # 第二遍：扫描章节标题与题目起始行
    chapters = {}          # name -> {"part":..., "name":..., "q_ranges": [...]}
    chapter_order = []
    current_part = ""
    current_section = ""
    current_chapter = None
    q_starts = []          # (line_idx, num)

    i = 0
    while i < len(lines):
        s = lines[i]
        if PART_MARK.match(s):
            # 下一非空行是部分标题
            j = i + 1
            while j < len(lines) and not lines[j]:
                j += 1
            current_part = clean_text(lines[j]) if j < len(lines) else ""
            current_section = ""
            current_chapter = current_part
            i = j + 1
            continue
        if SECTION_MARK.match(s):
            j = i + 1
            while j < len(lines) and not lines[j]:
                j += 1
            current_section = clean_text(lines[j]) if j < len(lines) else ""
            current_chapter = current_section or current_part
            i = j + 1
            continue
        if PRACTICE_MARK.match(s):
            base = current_section or current_part
            current_chapter = f"{base}·课后练习" if base else "课后练习"
            i += 1
            continue
        m = Q_START.match(s)
        if m:
            q_starts.append((i, int(m.group(1)), current_chapter or "未分类"))
        i += 1

    # 章节标题行集合（题目块的截止边界）
    boundary = set()
    for idx, ln in enumerate(lines):
        if PART_MARK.match(ln) or SECTION_MARK.match(ln) or PRACTICE_MARK.match(ln):
            boundary.add(idx)

    # 第三遍：切分题目块并解析
    def parse_block(block_lines):
        text = "\n".join(block_lines)
        # 题干：开头到第一个选项行
        m_stem = re.match(r"^\d+\s*[.．]\s*（单选）(.*?)(?=^[A-D][.．]|\Z)", text, re.S | re.M)
        stem = clean_text(m_stem.group(1)) if m_stem else ""
        # 选项
        options = []
        for m in re.finditer(r"^([A-D])[.．](.*?)(?=^[A-D][.．]|^【答案】|\Z)", text, re.S | re.M):
            options.append([m.group(1), clean_text(m.group(2))])
        # 答案与解析
        answer, analysis = "", ""
        m_ans = re.search(r"【答案】\s*([A-D])\s*[。.]?\s*(.*)", text, re.S)
        if m_ans:
            answer = m_ans.group(1)
            analysis = clean_text(m_ans.group(2))
        return stem, options, answer, analysis

    problems = []
    for k, (start, num, chap) in enumerate(q_starts):
        end = q_starts[k + 1][0] if k + 1 < len(q_starts) else len(lines)
        # 截到最近的边界（章节标题）
        for b in sorted(boundary):
            if start < b < end:
                end = b
                break
        block = [x for x in lines[start:end] if x]
        stem, options, answer, analysis = parse_block(block)
        problems.append({
            "chapter": chap, "num": num, "page": pages[start],
            "stem": stem, "options": options, "answer": answer, "analysis": analysis,
        })

    # 组装章节
    for p in problems:
        name = p["chapter"]
        if name not in chapters:
            chapters[name] = {"name": name, "questions": []}
            chapter_order.append(name)
        chapters[name]["questions"].append(p)

    result_chapters = []
    for cid, name in enumerate(chapter_order, 1):
        ch = chapters[name]
        qs = []
        for q in ch["questions"]:
            qs.append({
                "id": f"c{cid}q{len(qs) + 1}",
                "num": q["num"],
                "type": "single",
                "stem": q["stem"],
                "options": q["options"],
                "answer": q["answer"],
                "analysis": q["analysis"],
                "page": q["page"],
            })
        result_chapters.append({"id": f"c{cid}", "name": name, "questions": qs})

    data = {
        "title": f"{name}题库",
        "source": name,
        "total": sum(len(c["questions"]) for c in result_chapters),
        "chapters": result_chapters,
    }
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    # 同步生成小程序数据文件（目录存在时）
    if OUT_JS.parent.exists():
        OUT_JS.write_text(
            "module.exports = %s;" % json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    # 验证报告
    print(f"章节数: {len(result_chapters)}, 总题数: {data['total']}")
    bad = []
    for c in result_chapters:
        print(f"  [{c['id']}] {c['name']}: {len(c['questions'])} 题")
        for q in c["questions"]:
            letters = [o[0] for o in q["options"]]
            if not q["stem"] or q["answer"] not in letters or len(letters) < 2:
                bad.append((c["name"], q["num"], q["stem"][:30], letters, q["answer"]))
            if any(not o[1] for o in q["options"]):
                bad.append((c["name"], q["num"], "选项文本为空", letters, q["answer"]))
    if bad:
        print(f"\n异常题目 {len(bad)} 个:")
        for b in bad[:10]:
            print(" ", b)
    else:
        print("\n验证通过：所有题目均有题干、>=2个选项、答案在选项内")

    # 预览文件
    with OUT_PREVIEW.open("w", encoding="utf-8") as f:
        f.write(f"# {data['title']}（共 {data['total']} 题）\n\n")
        for c in result_chapters:
            f.write(f"## {c['name']}（{len(c['questions'])} 题）\n\n")
            for q in c["questions"][:2]:
                f.write(f"**{q['num']}.** {q['stem']}\n\n")
                for letter, txt in q["options"]:
                    f.write(f"- {letter}. {txt}\n")
                f.write(f"\n**答案：{q['answer']}**　解析：{q['analysis'][:120]}…\n\n---\n\n")
    print(f"预览已写入: {OUT_PREVIEW}")
    if OUT_JS.parent.exists():
        print(f"小程序数据已写入: {OUT_JS}")


if __name__ == "__main__":
    main()
