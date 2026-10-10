# -*- coding: utf-8 -*-
"""生成演示题库数据（12 道自行编写的北京市情题目，供开源仓库演示使用）

写入两个文件：
  - questions.json                        题库中间产物
  - shuati-miniprogram/data/questions.js  小程序加载的数据文件

默认不覆盖已存在的文件（避免误毁你自己的真实题库），加 --force 强制覆盖。
要使用自己的资料生成题库，请走 extract_text.py → parse_questions.py 流程。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT_JSON = ROOT / "questions.json"
OUT_JS = ROOT / "shuati-miniprogram" / "data" / "questions.js"


def q(ch, num, stem, options, answer, analysis):
    return {
        "id": f"c{ch}q{num}",
        "num": num,
        "type": "single",
        "stem": stem,
        "options": [list(o) for o in options],
        "answer": answer,
        "analysis": analysis,
        "page": 0,
    }


CH1 = [
    q(1, 1, "北京市的市花是（）。",
      [("A", "月季和菊花"), ("B", "牡丹和月季"), ("C", "菊花和梅花"), ("D", "百合和牡丹")], "A",
      "1987 年北京市确定月季、菊花为市花，侧柏、国槐为市树。"),
    q(1, 2, "北京市的市树是（）。",
      [("A", "银杏和侧柏"), ("B", "国槐和银杏"), ("C", "侧柏和国槐"), ("D", "杨树和柳树")], "C",
      "侧柏和国槐是北京市树，其中国槐栽培历史悠久，是北京的乡土树种。"),
    q(1, 3, "北京市的土地总面积约为（）。",
      [("A", "6410 平方千米"), ("B", "16410 平方千米"), ("C", "26410 平方千米"), ("D", "36410 平方千米")], "B",
      "北京市土地总面积约 16410 平方千米。"),
    q(1, 4, "北京市现辖（）个市辖区。",
      [("A", "14"), ("B", "15"), ("C", "16"), ("D", "17")], "C",
      "北京市辖东城、西城、朝阳、海淀、丰台、石景山、门头沟、房山、通州、顺义、昌平、大兴、怀柔、平谷、密云、延庆共 16 个区。"),
    q(1, 5, "下列不属于北京「四个中心」城市战略定位的是（）。",
      [("A", "全国政治中心"), ("B", "全国文化中心"), ("C", "国际交往中心"), ("D", "全国经济中心")], "D",
      "北京「四个中心」指全国政治中心、文化中心、国际交往中心、科技创新中心，不包含「经济中心」。"),
    q(1, 6, "被称为北京「母亲河」的是（）。",
      [("A", "潮白河"), ("B", "永定河"), ("C", "北运河"), ("D", "拒马河")], "B",
      "永定河流经北京西部、南部，是北京的母亲河。"),
    q(1, 7, "北京大兴国际机场于（）年正式投运。",
      [("A", "2017"), ("B", "2018"), ("C", "2019"), ("D", "2020")], "C",
      "北京大兴国际机场于 2019 年 9 月 25 日正式投运，被誉为「凤凰展翅」。"),
]

CH2 = [
    q(2, 1, "2024 年 7 月，北京成功列入《世界遗产名录》的项目是（）。",
      [("A", "颐和园"), ("B", "北京中轴线"), ("C", "明十三陵"), ("D", "大运河北京段")], "B",
      "2024 年 7 月 27 日，「北京中轴线——中国理想都城秩序的杰作」列入《世界遗产名录》，北京世界遗产增至 8 处。"),
    q(2, 2, "成功举办 2022 年冬奥会后，北京获得的称号是（）。",
      [("A", "奥运之城"), ("B", "双奥之城"), ("C", "冰雪之都"), ("D", "体育之都")], "B",
      "北京是全球首个既举办过夏季奥运会又举办过冬季奥运会的城市，被称为「双奥之城」。"),
    q(2, 3, "北京「两区」建设指的是（）。",
      [("A", "国家服务业扩大开放综合示范区和自由贸易试验区"),
       ("B", "经济特区和新区"),
       ("C", "高新技术产业开发区和经济技术开发区"),
       ("D", "综合保税区和自贸区")], "A",
      "「两区」指国家服务业扩大开放综合示范区、中国（北京）自由贸易试验区。"),
    q(2, 4, "北京环球度假区位于（）。",
      [("A", "朝阳区"), ("B", "海淀区"), ("C", "通州区"), ("D", "大兴区")], "C",
      "北京环球度假区位于通州区，2021 年 9 月 20 日正式开园。"),
    q(2, 5, "「首都功能核心区」指的是（）。",
      [("A", "东城区和西城区"), ("B", "朝阳区和海淀区"), ("C", "丰台区和石景山区"), ("D", "通州区和大兴区")], "A",
      "首都功能核心区包括东城区、西城区，总面积约 92.5 平方千米。"),
]

DEMO = {
    "title": "北京市情演示题库",
    "source": "演示数据（generate_demo_data.py 生成）",
    "total": len(CH1) + len(CH2),
    "chapters": [
        {"id": "c1", "name": "北京基本市情（演示）", "questions": CH1},
        {"id": "c2", "name": "时事与新进展（演示）", "questions": CH2},
    ],
}


def main():
    force = "--force" in sys.argv
    existing = [p for p in (OUT_JSON, OUT_JS) if p.exists()]
    if existing and not force:
        print("检测到已存在题库文件，跳过生成（如需覆盖请加 --force）：")
        for p in existing:
            print("  -", p.relative_to(ROOT))
        return

    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(DEMO, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_JS.write_text(
        "module.exports = %s;" % json.dumps(DEMO, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"演示题库已生成：{len(DEMO['chapters'])} 章 / {DEMO['total']} 题")
    print("  -", OUT_JSON.relative_to(ROOT))
    print("  -", OUT_JS.relative_to(ROOT))
    print("现在可用微信开发者工具打开 shuati-miniprogram 目录编译运行")


if __name__ == "__main__":
    main()
