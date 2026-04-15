# github-epub-productizer

把 GitHub 上的书籍型 Markdown 仓库整理成可售卖的数字商品。

当前 skill 自带 3 类能力：

1. EPUB 生成
2. 商品销售文案
3. 商品图生成

## 目录结构

```text
github-epub-productizer/
├── SKILL.md
├── README.md
├── scripts/
│   ├── gen_epub_enhanced.py
│   ├── gen_cover_html.py
│   ├── gen_cover_svg.py
│   ├── generate_multiref_poster.py
│   ├── make_seag_product_poster_html.py
│   └── render_html_poster.py
└── references/
    ├── Gemini-API-生图使用规范.md
    └── 2026-04-15_Gemini多参考图生图踩坑记录.md
```

## 脚本说明

### EPUB

- `scripts/gen_epub_enhanced.py`
  默认 EPUB 生成器，支持本地图片、Markdown 渲染、目录生成。

- `scripts/gen_cover_html.py`
  EPUB HTML 封面相关辅助脚本。

- `scripts/gen_cover_svg.py`
  EPUB SVG 封面相关辅助脚本。

`gen_epub_enhanced.py` 会依赖 `gen_cover_html.py` 和 `gen_cover_svg.py`，所以这 3 个脚本必须一起保留。

### 商品图

- `scripts/generate_multiref_poster.py`
  Gemini 多参考图商品海报生成，默认优先使用：
  - `gemini-3.1-flash-image-preview`
  - `gemini-3-pro-image-preview`

- `scripts/make_seag_product_poster_html.py`
  生成 HTML 商品图模板。

- `scripts/render_html_poster.py`
  用 Playwright 把 HTML 商品图截图成 PNG。

## 参考文档

- `references/Gemini-API-生图使用规范.md`
  Gemini API 生图的通用做法，强调“少写要求，多给准确参考图”。

- `references/2026-04-15_Gemini多参考图生图踩坑记录.md`
  这次项目里沉淀下来的关键 bug 经验，解释为什么“多参考图”比“文本 prompt + 拼图脚本”更有效。

## 说明

这个 skill 现在已经不依赖外部 skill 目录里的脚本路径来工作，核心依赖都已经复制到本目录。

## 使用前准备

如果你只需要生成 `.epub`，不需要额外准备生图 API key，EPUB 功能可以独立工作。

如果你还想生成商品图，需要准备一个**可生图的 API key**。默认推荐 Gemini，因为当前这套 skill 的多参考图商品海报流程就是围绕 Gemini 预览模型设计的。

默认要求：

- 有可用的 Gemini 图片模型 API key
- shell 环境中已设置对应环境变量

Gemini API key 不放在 skill 里，默认从环境变量读取：

- `GEMINI_API_KEY`

可在本机：

- `~/.zshrc`

中找到对应配置来源。

如果没有可用的生图 API key：

- 商品图功能无法正常调用 Gemini 多参考图生成
- 但 `.epub` 电子书仍然可以正常生成
- 销售文案也不受影响

这时可以：

- 只生成 `.epub` 和文案
- 或改走 HTML 商品图模板路线
