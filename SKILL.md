---
name: github-epub-productizer
description: Turn a GitHub-hosted book or long Markdown repository into a sellable digital product. Use this whenever the user wants to make an EPUB from a GitHub repo, package a repo/book for sale, generate a product description, or create a Chinese ecommerce-style product poster for an ebook. This skill is especially appropriate when the workflow includes EPUB generation, sales copy, and Gemini-based poster generation in one pass.
---

# GitHub EPUB Productizer

把一个 GitHub 上的书籍/长 Markdown 仓库，整理成可售卖的数字商品。

默认覆盖 3 件事：

1. 生成 EPUB
2. 生成销售文案
3. 生成商品图

## 先看目标

这个 skill 不是单纯“导出 epub”，而是把一本 GitHub 上的书做成一套可出售的商品资产。

默认输出包括：

- `source/` 原始仓库
- `build/` 中间整理内容
- `output/*.epub`
- `output/*销售文案.md`
- `output/*商品图.png`

## 适用场景

适合：

- GitHub 仓库本身就是 Markdown 章节书
- 有 `_sidebar.md`、目录文件或明确章节顺序
- 用户想把内容做成 EPUB
- 用户还想顺手生成商品页文案和商品图

不适合：

- 纯 PDF 扫描件
- 版权来源不清晰、仓库内容不完整
- 目标是严格出版排版，而不是“可读、可卖、可展示”

## 默认工作流

### Step 1：准备书籍工作区

在项目内建立工作目录：

```text
03-Projects/epub-book-pipeline/books/<book-slug>/
  source/
  build/
  output/
```

如果是已有项目，优先复用现有目录，不重复新建。

### Step 2：拉取 GitHub 仓库

把原始仓库放进 `source/`。

优先确认：

- 目录真相源是什么（如 `_sidebar.md`）
- 是否存在图片资源
- 是否是 Markdown 为主，而不是网页壳子

### Step 3：整理 build

目标是给 EPUB 生成器一个干净、顺序明确的输入目录。

最低要求：

- 按章节顺序输出 `.md`
- 给每章补稳定标题
- 修正本地图片路径
- 保留必要资源

如果仓库是 docsify/docs 风格，优先从 `_sidebar.md` 抽章节顺序。

### Step 4：生成 EPUB

默认调用：

- `scripts/gen_epub_enhanced.py`

默认参数思路：

- 保留目录顺序
- 优先保留本地图
- 图片宽度 `1000`
- 图片质量 `88`
- 输出到 `output/`

如果书本身已有合适封面，优先直接用，不要重复生成花哨封面。

### Step 5：生成销售文案

文案目标不是写长文章，而是写适合商品页的描述。

默认要求：

- 中等长度
- 强转化
- 少空话
- 重点突出“这是什么、适合谁、为什么值得买”

如果用户没有要求特定风格，默认写“商品页转化文案”，不是内容作者个人风格。

### Step 6：生成商品图

商品图默认分两条路：

#### 默认优先：Gemini 多参考图

优先使用：

1. `gemini-3.1-flash-image-preview`
2. `gemini-3-pro-image-preview`

不要默认退回 `gemini-2.5-flash-image`。

默认做法：

- 提供一句清楚任务描述
- 提供 1 到 3 张参考图
- 明确每张参考图分别负责什么
- 优先调用 `scripts/generate_multiref_poster.py`

优先参考：

- `references/Gemini-API-生图使用规范.md`
- `references/2026-04-15_Gemini多参考图生图踩坑记录.md`

原则：

- 少写要求
- 多给准确参考图
- 不要把 prompt 写成布局程序

#### 稳定 fallback：HTML/CSS -> PNG

当出现以下情况时，改用 HTML：

- 小字很多
- 文案必须完全可读
- 需要固定模板
- 需要一键下载 PNG

HTML 相关脚本可优先用：

- `scripts/make_seag_product_poster_html.py`
- `scripts/render_html_poster.py`

HTML 适合做稳定商品图模板，不适合替代 Gemini 的整图创意能力。

## 关于 Gemini API Key

Gemini API key 可从：

- `~/.zshrc`

中找到。

脚本调用时优先读取环境变量：

- `GEMINI_API_KEY`

不要把 key 写入 skill、脚本或项目文件。

如果用户没有可用的图片 API key：

- `.epub` 仍然可以正常生成
- 销售文案仍然可以正常生成
- 商品图应优先改走 HTML/CSS -> PNG fallback

## 默认产物清单

完成后至少应有：

- 一个 `.epub`
- 一份销售文案 Markdown
- 一张商品图
- 一份 prompt / model 记录（如果用了 Gemini）

## 常见坑

- 直接把 GitHub 仓库丢给 EPUB 生成器，不做中间整理
- 商品图只写长 prompt，不给参考图
- 把 Gemini 当成“背景生成器”，再用脚本硬拼整图
- 小字很多却还坚持纯 Gemini 生成，不切 HTML
- 把参考图上传了，但没说明每张图的角色

## 一句话版本

这个 skill 的默认目标不是“生成一本 epub”，而是“把一本 GitHub 上的书做成一套能卖的数字商品”。
