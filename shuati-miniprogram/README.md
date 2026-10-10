# 北京市情刷题 · 微信小程序

基于《北京市情时政（更新至8月）》PDF 自动提取的 225 道单选题打造的刷题小程序。

## 功能

- **顺序练习**：14 个章节（政府工作报告 60 题 / 12 个月时政各 5 题 / 市情习题 105 题），自动续到上次未做的位置
- **随机刷题**：全题库打乱顺序
- **错题本**：答错自动收录，重新答对自动移出
- **蒙对标记**：答对但没把握的题可标记「🎲 蒙对」，同样保留在错题本继续攻克；重新作答后标记重置，答对可再次标记
- **即时判定**：点选项立刻判分（对绿错红）+ 震动反馈，随后展示完整解析
- **进度统计**：首页展示已练题数、正确率、各章节进度条
- **记录持久化**：答题记录存本地缓存（wx.storage），关掉小程序不丢失；首页可一键清空

## 如何运行

1. 先在仓库根目录生成题库数据（二选一）：
   - 演示题库：`python generate_demo_data.py`
   - 自己的资料：`python extract_text.py 资料.pdf` → `python parse_questions.py 资料_提取文本.txt`
2. 下载安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
3. 打开开发者工具 → 「导入项目」→ 项目目录选择本文件夹（`shuati-miniprogram`）
4. AppID 选「游客模式 / 测试号」即可（`project.config.json` 已配置 `touristappid` 占位）
5. 点击「编译」即可在模拟器中刷题

> 游客模式仅支持模拟器。真机预览或正式发布：在 [微信公众平台](https://mp.weixin.qq.com/) 注册小程序账号（个人免费），在开发者工具「详情 → 基本信息」中改成你自己的 AppID——改动写入 `project.private.config.json`（已被 git 忽略，不会泄露到仓库），再用「上传」提交代码审核。

## 目录结构

```
shuati-miniprogram/
├── app.js / app.json / app.wxss     # 小程序入口与全局配置
├── project.config.json              # 项目配置（测试号 appid）
├── sitemap.json
├── data/
│   └── questions.js                 # 题库数据（225 题，124KB）
├── utils/
│   └── store.js                     # 答题记录/错题本/统计（本地缓存）
└── pages/
    ├── index/                       # 首页：统计 + 章节列表 + 模式入口
    └── quiz/                        # 答题页：判定 + 解析 + 上一题/下一题
```

## 题库更新

数据文件 `data/questions.js` 不随仓库分发，在**仓库根目录**生成：

```bash
# 演示题库（12 道自编题）
python generate_demo_data.py

# 或用自己的资料（电子版 PDF 两步生成，自动写入 data/questions.js）
python extract_text.py ../你的资料.pdf
python parse_questions.py ../你的资料_提取文本.txt
```

扫描件 PDF 先用 `../ocr_pdf.py`（OvisOCR2）做 OCR，再走上述解析流程。详见根目录 README。
