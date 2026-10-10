# 北京市情刷题 · 微信小程序

一条「**文档 → 题库 → 小程序**」的完整流水线：从 PDF 学习资料自动解析出结构化题库，并生成一个开箱即用的微信小程序刷题应用。

仓库自带演示题库生成器，**克隆后无需任何私有数据即可跑通全流程**；也可以用你自己的资料生成专属题库。

## ✨ 功能

**小程序端**

- 📖 **顺序练习**：章节列表 + 进度条，自动续到上次未答的题目
- 🎲 **随机刷题**：全题库打乱重做
- 📕 **错题本**：答错自动收录，重做答对自动移出
- 🎯 **蒙对标记**：答对但没把握的题可标记「🎲 蒙对」，继续保留在错题本攻克
- ⚡ **即时反馈**：点选项立刻判分（对绿错红）+ 震动，随后展示完整解析
- 📊 **进度统计**：已练数 / 正确率 / 错题数 / 各章节进度，本地持久化
- ✅ **纯 Node 逻辑测试**：无需微信开发者工具即可跑通错题本/蒙对标记的 18 项断言

**题库流水线**

- 电子版 PDF：PyMuPDF 直接提取文字层（无损、秒级）
- 扫描件 PDF：内置 [OvisOCR2](https://modelscope.cn/models/ATH-MaaS/OvisOCR2)（OmniDocBench v1.6 SOTA，0.8B 参数，8GB 显存可跑）推理脚本
- 正则解析：自动识别章节 / 题干 / 选项 / 【答案】/ 解析，输出结构化 JSON 并一键转为小程序数据文件

## 🚀 快速开始

前置：[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)、Python 3.8+

```bash
git clone <仓库地址> && cd shuati_project

# 1. 生成演示题库（12 道自编北京市情题）
python generate_demo_data.py

# 2. 微信开发者工具 →「导入项目」→ 选择 shuati-miniprogram/ 目录
#    AppID 选「游客模式 / 测试号」即可（仓库已配置 touristappid 占位）
# 3. 点「编译」，在模拟器中开始刷题
```

> 游客模式（`touristappid`）仅支持模拟器调试。真机预览或发布，需在[微信公众平台](https://mp.weixin.qq.com/)注册自己的小程序 AppID（个人主体免费），然后在开发者工具「详情 → 基本信息」中修改——改动会写入 `project.private.config.json`，该文件已被 git 忽略，**不会把你的 AppID 提交进仓库**。

运行逻辑测试（可选，需 Node.js）：

```bash
node test_quiz_logic.js
# 覆盖：错题本重做自动移出 / 蒙对标记进出错题本 / 章节续做与回看 / 统计口径一致性
```

## 🛠 自制题库

输入文本的格式约定（`parse_questions.py` 按此解析）：

```
第一部分
2026年北京市政府工作报告
1.（单选）题干内容（）。
A. 选项A
B. 选项B
C. 选项C
D. 选项D
【答案】D 解析内容（可选，跟在答案后即可）
```

生成流程（电子版 PDF 两步搞定）：

```bash
pip install pymupdf

python extract_text.py 你的资料.pdf            # → 你的资料_提取文本.txt
python parse_questions.py 你的资料_提取文本.txt  # → questions.json + 题库预览.md
                                               #   + shuati-miniprogram/data/questions.js
# 回到微信开发者工具点「编译」即可
```

解析脚本会输出验证报告（章节数、每章题数、异常题目检查），生成后可打开 `题库预览.md` 抽查内容。

> ⚠️ **题目 id 稳定性**：小程序的本地答题记录按题目 id（如 `c3q5` = 第 3 章第 5 题）存储。更新题库时请尽量保持章节结构与题号顺序不变，否则旧记录会错位关联到新题。

### 扫描件 PDF：OvisOCR2 OCR

电子版 PDF 请优先用文字层直提（无损且瞬时）；只有扫描件才需要 OCR。

```bash
# GPU 版 PyTorch（按你的 CUDA 版本调整，8GB 显存即可）
pip install torch --index-url https://download.pytorch.org/whl/cu130
pip install "transformers>=4.57" pymupdf pillow modelscope

# 下载模型（约 1.6GB）
python -c "from modelscope import snapshot_download; snapshot_download('ATH-MaaS/OvisOCR2', local_dir='models/OvisOCR2')"

# OCR：每页渲染为 200dpi 图片 → 模型识别 → 输出 Markdown
python ocr_pdf.py 你的扫描件.pdf              # → 你的扫描件_OCR结果.md
```

> ⚠️ Windows + transformers 后端速度较慢（实测约 10 分钟/页，GDN 线性注意力层未优化）。批量处理建议按官方指引在 Linux 上用 vLLM 部署。OCR 产物需整理为上文「格式约定」的文本后再进解析流程。

## 📁 项目结构

```
shuati_project/
├── shuati-miniprogram/          # 微信小程序（原生框架，无第三方依赖）
│   ├── app.js / app.json / app.wxss
│   ├── project.config.json      # 公共配置（AppID 为 touristappid 占位）
│   ├── data/questions.js        # 题库数据（git 忽略，由脚本生成）
│   ├── utils/store.js           # 答题记录 / 错题本 / 蒙对标记（wx.storage）
│   └── pages/
│       ├── index/               # 首页：统计 + 模式入口 + 章节列表
│       └── quiz/                # 答题页：判定 + 解析 + 蒙对开关 + 上下题
├── extract_text.py              # 电子版 PDF → 文字层提取
├── parse_questions.py           # 提取文本 → 结构化题库（JSON + 小程序数据）
├── generate_demo_data.py        # 生成演示题库（12 道自编题）
├── ocr_pdf.py                   # 扫描件 PDF → Markdown（OvisOCR2 推理）
├── test_quiz_logic.js           # 小程序逻辑测试（mock wx 环境，18 项断言）
├── questions.json               # 题库中间产物（git 忽略）
└── models/OvisOCR2/             # OCR 模型权重（git 忽略，自行下载）
```

## 💾 数据存储

- 答题记录保存在小程序本地缓存（`wx.setStorageSync`，key `sq_answers`），纯前端方案，无需服务器
- 小程序**发新版本不丢记录**；用户删除小程序、清理微信缓存或换手机时记录会丢失
- 记录按题目 id 存储，单题只保留最新一次作答（重做覆盖）
- 需要跨设备同步时，可升级为微信云开发：把 `utils/store.js` 的读写迁移到云数据库，页面逻辑基本不用动

## 🚫 仓库不包含的内容

以下内容已被 `.gitignore` 排除，原因与获取方式：

| 排除内容 | 原因 | 获取 / 生成方式 |
|---|---|---|
| `models/`（OvisOCR2 权重，约 1.6GB） | 超过 GitHub 单文件 100MB 上限；模型属于第三方 | ModelScope 下载 `ATH-MaaS/OvisOCR2`（见上文） |
| 原始 PDF、`*_提取文本.txt` | 第三方版权内容 | 使用你自己的资料 |
| `questions.json`、`题库预览.md`、`parse_report.txt` | 版权资料的衍生数据 | `python parse_questions.py <文本>` |
| `shuati-miniprogram/data/questions.js` | 同上 | `python generate_demo_data.py`（演示）或解析流程 |
| `shuati-miniprogram/project.private.config.json` | 含个人 AppID 与私有设置 | 开发者工具自动生成 |
| `.claude/` | 本地 AI 辅助工具配置 | — |

若你**拥有题库内容的版权或已获授权**，删除 `.gitignore` 中对应行即可把真实题库随仓库发布。

## ⚖️ License 与免责声明

代码以 [MIT](LICENSE) 协议开源。

- 演示题库（`generate_demo_data.py`）内容为项目作者自行编写，仅作功能演示
- 本项目**不分发任何第三方资料内容**；仓库开发过程中使用的原始 PDF 及其题库均由使用者本地生成
- 使用自己的资料生成题库时，请遵守相关版权法规，仅供个人学习使用

## 🙏 致谢

- [OvisOCR2](https://modelscope.cn/models/ATH-MaaS/OvisOCR2) — OmniDocBench v1.6 SOTA 文档解析模型
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF 文字层提取与页面渲染
