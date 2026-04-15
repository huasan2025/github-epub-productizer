#!/usr/bin/env python3
"""
Enhanced EPUB generator with image downloading and better Markdown rendering.

Key improvements:
1. Downloads all images from Markdown (http/https URLs) and embeds them
2. Better code block styling with syntax highlighting
3. Table support with proper styling
4. Preserves all Markdown elements (lists, blockquotes, etc.)

Usage:
    python3 gen_epub_enhanced.py <input_dir> <output.epub> [options]
"""

import argparse
import os
import glob
import re
import sys
import html as html_module
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from ebooklib import epub
import markdown
from PIL import Image
import io


# Enhanced CSS with code block and table styling
CHAPTER_CSS = """
body {
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
    line-height: 1.8;
    margin: 1em;
    padding: 0;
    font-size: 1em;
    color: #1a1a1a;
}
h1 {
    font-size: 1.6em;
    font-weight: bold;
    margin: 0 0 0.5em 0;
    color: #111;
    line-height: 1.3;
}
h2 {
    font-size: 1.3em;
    font-weight: bold;
    margin: 1.5em 0 0.5em 0;
    color: #222;
}
h3 {
    font-size: 1.1em;
    font-weight: bold;
    margin: 1.2em 0 0.4em 0;
    color: #333;
}
h4 {
    font-size: 1.05em;
    font-weight: bold;
    margin: 1em 0 0.3em 0;
    color: #444;
}
p {
    margin: 0 0 0.8em 0;
    text-align: justify;
}
strong, b {
    font-weight: bold;
    color: #000;
}
em, i {
    font-style: italic;
}
blockquote {
    border-left: 3px solid #ccc;
    padding-left: 1em;
    margin: 1em 0;
    color: #444;
    background: #f9f9f9;
}
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}
.metadata {
    color: #666;
    font-size: 0.85em;
    margin-bottom: 1em;
}
.card-img {
    text-align: center;
    margin: 1em 0;
}
hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 1.5em 0;
}
/* Code blocks */
pre {
    background: #f8f8f8;
    border-left: 3px solid #0066cc;
    border-radius: 4px;
    padding: 1em;
    overflow-x: auto;
    margin: 1em 0;
    font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code", "Fira Mono",
                 "Roboto Mono", "Consolas", "Courier New", monospace;
    font-size: 0.85em;
    line-height: 1.4;
    tab-size: 2;
}
code {
    font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code", "Fira Mono",
                 "Roboto Mono", "Consolas", "Courier New", monospace;
    font-size: 0.9em;
    background: #f0f0f0;
    padding: 0.2em 0.4em;
    border-radius: 3px;
}
pre code {
    background: none;
    padding: 0;
}
/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    font-size: 0.9em;
}
th, td {
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
}
th {
    background-color: #0066cc;
    color: white;
    font-weight: bold;
}
tbody tr:nth-child(even) {
    background-color: #f8f9fa;
}
tbody tr:hover {
    background-color: #f0f0f0;
}
/* Lists */
ul, ol {
    margin: 0.5em 0 1em 1.5em;
    padding: 0;
}
li {
    margin: 0.3em 0;
}
/* Override Pygments error token red border */
.codehilite span[style*="border: 1px solid #FF0000"] {
    border: none !important;
}
"""


def compress_image(img_data_or_path, target_width=1000, jpeg_quality=88):
    """Compress image to JPEG with configurable quality."""
    try:
        if isinstance(img_data_or_path, bytes):
            img = Image.open(io.BytesIO(img_data_or_path))
        else:
            img = Image.open(img_data_or_path)

        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        if img.width > target_width:
            ratio = target_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)

        output = io.BytesIO()
        img.save(output, format='JPEG', quality=jpeg_quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"  Warning: Image compression failed: {e}")
        return None


def convert_svg_to_png(svg_data, width=1000):
    """Convert SVG data to PNG using Playwright headless browser."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  Warning: Playwright not installed, cannot convert SVG")
        return None

    try:
        import tempfile
        # Write SVG to temp file
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False, mode='wb') as f:
            f.write(svg_data)
            svg_path = f.name

        png_path = svg_path.replace('.svg', '.png')

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 800})
            page.goto(f"file://{svg_path}")
            page.wait_for_timeout(1000)

            # Get the SVG element dimensions
            dimensions = page.evaluate("""() => {
                const svg = document.querySelector('svg');
                if (!svg) return null;
                const rect = svg.getBoundingClientRect();
                return { width: rect.width, height: rect.height };
            }""")

            if dimensions:
                # Resize viewport to fit SVG
                page.set_viewport_size({
                    "width": max(int(dimensions['width']), 200),
                    "height": max(int(dimensions['height']), 100)
                })
                page.wait_for_timeout(300)

            page.screenshot(path=png_path, full_page=True)
            browser.close()

        with open(png_path, 'rb') as f:
            png_data = f.read()

        # Clean up temp files
        os.unlink(svg_path)
        os.unlink(png_path)

        return png_data
    except Exception as e:
        print(f"  Warning: SVG conversion failed: {e}")
        return None


# Shared Playwright browser instance for batch SVG conversion
_svg_browser = None
_svg_playwright = None


def _get_svg_browser():
    """Get or create a shared Playwright browser for SVG conversion."""
    global _svg_browser, _svg_playwright
    if _svg_browser is None:
        try:
            from playwright.sync_api import sync_playwright
            _svg_playwright = sync_playwright().start()
            _svg_browser = _svg_playwright.chromium.launch(headless=True)
        except Exception as e:
            print(f"  Warning: Cannot start Playwright for SVG: {e}")
            return None
    return _svg_browser


def _close_svg_browser():
    """Close shared Playwright browser."""
    global _svg_browser, _svg_playwright
    if _svg_browser:
        _svg_browser.close()
        _svg_browser = None
    if _svg_playwright:
        _svg_playwright.stop()
        _svg_playwright = None


def convert_svg_to_png_fast(svg_data, width=1000):
    """Convert SVG to PNG reusing a shared browser instance (faster for batch)."""
    browser = _get_svg_browser()
    if not browser:
        return None

    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False, mode='wb') as f:
            f.write(svg_data)
            svg_path = f.name

        png_path = svg_path.replace('.svg', '.png')
        page = browser.new_page(viewport={"width": width, "height": 800})

        try:
            page.goto(f"file://{svg_path}")
            page.wait_for_timeout(800)

            dimensions = page.evaluate("""() => {
                const svg = document.querySelector('svg');
                if (!svg) return null;
                const rect = svg.getBoundingClientRect();
                return { width: rect.width, height: rect.height };
            }""")

            if dimensions:
                page.set_viewport_size({
                    "width": max(int(dimensions['width']), 200),
                    "height": max(int(dimensions['height']), 100)
                })
                page.wait_for_timeout(300)

            page.screenshot(path=png_path, full_page=True)
        finally:
            page.close()

        with open(png_path, 'rb') as f:
            png_data = f.read()

        os.unlink(svg_path)
        os.unlink(png_path)
        return png_data
    except Exception as e:
        print(f"  Warning: SVG conversion failed: {e}")
        return None


def download_image(url, timeout=15):
    """Download image from URL or read from local file, converting SVG to PNG via Playwright."""
    try:
        # Skip blob:, data: URLs
        if url.startswith('blob:') or url.startswith('data:'):
            return None

        url_path = url.split('?')[0].lower()
        is_svg = url_path.endswith('.svg')

        # Handle local file paths
        if url.startswith('/') or url.startswith('./') or url.startswith('../'):
            if not os.path.exists(url):
                print(f"  Warning: Local file not found: {url}")
                return None
            with open(url, 'rb') as f:
                data = f.read()
            content_type = 'image/png' if url.lower().endswith('.png') else 'image/jpeg'
        else:
            # Handle remote URLs
            # Strip CDN webp conversion params to get original format
            # e.g. alipayobjects ?x-oss-process=image/auto-orient,1/resize,w_2000/format,webp
            clean_url = url
            if not is_svg and ('format,webp' in url or 'format/webp' in url):
                # Try to get original format by removing format conversion
                clean_url = re.sub(r'/format,webp', '', url)
                clean_url = re.sub(r'/format/webp', '', clean_url)
                # Also cap resize to reasonable width
                clean_url = re.sub(r'/resize,w_\d+', '/resize,w_1200', clean_url)

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'image/png, image/jpeg, image/webp, image/svg+xml, image/*'
            }
            req = urllib.request.Request(clean_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content_type = response.headers.get('Content-Type', '')
                data = response.read()

        # Detect SVG content (by URL extension, content-type, or data signature)
        is_svg_content = (
            is_svg
            or 'svg' in content_type
            or data[:5] == b'<?xml'
            or data[:4] == b'<svg'
            or (data[:200].find(b'<svg') >= 0)
        )

        if is_svg_content:
            print(f"    Converting SVG: {url_path.split('/')[-1]}")
            png_data = convert_svg_to_png_fast(data)
            if png_data:
                return png_data
            else:
                print(f"  Warning: SVG conversion failed for: {url_path.split('/')[-1]}")
                return None

        # Skip HTML error pages
        if content_type.startswith('text/html') or data[:15].lstrip().startswith(b'<!DOCTYPE'):
            print(f"  Skipping HTML error page from: {url[:60]}...")
            return None

        # Validate the data is a real image PIL can open
        try:
            img_test = Image.open(io.BytesIO(data))
            img_test.load()  # force decode; verify() consumes pointer and is less reliable
        except Exception:
            # Fallback: try stripping all query params
            base_url = url.split('?')[0]
            if base_url != url:
                req2 = urllib.request.Request(base_url, headers=headers)
                try:
                    with urllib.request.urlopen(req2, timeout=timeout) as response2:
                        data = response2.read()
                    # Validate fallback data too
                    img_test2 = Image.open(io.BytesIO(data))
                    img_test2.load()
                except Exception:
                    print(f"  Warning: Not a valid raster image: {url[:60]}...")
                    return None
            else:
                print(f"  Warning: Not a valid raster image: {url[:60]}...")
                return None

        return data
    except Exception as e:
        print(f"  Warning: Failed to download {url[:80]}...: {e}")
        return None


def extract_and_download_images(markdown_text, book, image_width=1000, jpeg_quality=88):
    """
    Extract image URLs from Markdown, download them, add to EPUB, and replace URLs.
    Returns: (modified_markdown, image_count, total_size)
    """
    # Find all image references: ![alt](url)
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = list(re.finditer(img_pattern, markdown_text))

    if not matches:
        return markdown_text, 0, 0

    downloaded_images = {}
    total_size = 0

    for match in matches:
        alt_text = match.group(1)
        img_url = match.group(2)

        # Skip if already processed
        if img_url in downloaded_images:
            continue

        # Download image
        img_data = download_image(img_url)
        if not img_data:
            continue

        # Compress image
        compressed_data = compress_image(img_data, image_width, jpeg_quality)
        if not compressed_data:
            continue

        # Generate unique filename
        url_hash = hashlib.md5(img_url.encode()).hexdigest()[:8]
        img_filename = f"images/img_{url_hash}.jpg"

        # Add to EPUB
        img_item = epub.EpubItem(
            uid=f"img_{url_hash}",
            file_name=img_filename,
            media_type="image/jpeg",
            content=compressed_data
        )
        book.add_item(img_item)

        downloaded_images[img_url] = img_filename
        total_size += len(compressed_data)

    # Replace URLs in Markdown
    def replace_url(match):
        alt_text = match.group(1)
        img_url = match.group(2)
        if img_url in downloaded_images:
            return f'![{alt_text}]({downloaded_images[img_url]})'
        return match.group(0)

    modified_markdown = re.sub(img_pattern, replace_url, markdown_text)

    return modified_markdown, len(downloaded_images), total_size


def parse_article(md_path):
    """Parse Markdown article, extract title and metadata, clean jina.ai headers."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for YAML frontmatter
    yaml_frontmatter = {}
    if content.startswith('---\n'):
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            try:
                import yaml
                yaml_frontmatter = yaml.safe_load(parts[1]) or {}
                content = parts[2]  # Use content after frontmatter
            except:
                pass  # If YAML parsing fails, continue with original content

    lines = content.strip().split('\n')

    title = yaml_frontmatter.get('title', "Untitled")
    metadata = ""
    body_start = 0

    # Clean jina.ai metadata headers
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Extract title from jina.ai format (if not from YAML)
        if line.startswith('Title:') and title == "Untitled":
            title = line.split(':', 1)[1].strip()
            i += 1
            continue

        # Skip jina.ai metadata lines
        if line.startswith('URL Source:') or line.startswith('Published Time:'):
            i += 1
            continue

        # Skip "Markdown Content:" marker
        if line.startswith('Markdown Content:'):
            body_start = i + 1
            break

        # Standard Markdown title (if not from YAML)
        if line.startswith('# ') and title == "Untitled":
            title = line[2:].strip()
            body_start = i + 1
            if i + 1 < len(lines) and lines[i + 1].startswith('> '):
                metadata = lines[i + 1][2:].strip()
                body_start = i + 2
            break

        # Skip empty lines at start
        if not line:
            i += 1
            continue

        # If we hit content without finding title, use first line
        if i < 5:
            i += 1
            continue

        # Give up searching for title
        body_start = i
        break

    body = '\n'.join(lines[body_start:]).strip()
    return title, metadata, body


def split_markdown_by_headers(content):
    """
    Split a single Markdown file into chapters based on ## headers.
    Returns: [(title, content), ...]
    """
    lines = content.split('\n')
    chapters = []
    current_title = None
    current_content = []

    for line in lines:
        # Match ## headers (second level)
        if line.startswith('## '):
            # Save previous chapter
            if current_title:
                chapters.append((current_title, '\n'.join(current_content).strip()))
            # Start new chapter
            current_title = line[3:].strip()
            current_content = [line]  # Include the header in content
        else:
            if current_title:
                current_content.append(line)
            # Skip content before first ## header

    # Save last chapter
    if current_title:
        chapters.append((current_title, '\n'.join(current_content).strip()))

    return chapters


def build_xhtml(title, metadata, image_html, body_html):
    """Build valid XHTML document with inline CSS."""
    escaped_title = html_module.escape(title)

    meta_section = ""
    if metadata:
        meta_section = f'<p class="metadata">{html_module.escape(metadata)}</p>'

    img_section = ""
    if image_html:
        img_section = f'<div class="card-img">{image_html}</div>'

    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>{escaped_title}</title>
<style type="text/css">
{CHAPTER_CSS}
</style>
</head>
<body>
<h1>{escaped_title}</h1>
{meta_section}
{img_section}
{body_html}
</body>
</html>"""


def fix_xhtml(html_str):
    """Fix common HTML issues for XHTML compatibility."""
    # Fix self-closing tags
    html_str = re.sub(r'<br\s*>', '<br/>', html_str)
    html_str = re.sub(r'<hr\s*>', '<hr/>', html_str)
    html_str = re.sub(r'<img([^/]*?)>', r'<img\1/>', html_str)

    # Remove Pygments error token red borders
    # Pygments marks unknown tokens with border: 1px solid #FF0000
    html_str = re.sub(r'border:\s*1px\s+solid\s+#FF0000;?\s*', '', html_str)

    # Fix remaining & symbols outside code blocks
    # Note: Pygments (codehilite) already escapes content inside <code> blocks,
    # so we only need to fix unescaped & in regular text
    html_str = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', html_str)

    return html_str


def generate_html_cover(title, subtitle="", author=""):
    """Generate cover image from HTML template using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Warning: Playwright not installed, skipping HTML cover generation")
        return None

    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from gen_cover_html import generate_cover_html, screenshot_cover

    html_path = generate_cover_html(title, subtitle, author)
    cover_path = "/tmp/epub_cover.jpg"
    screenshot_cover(html_path, cover_path)

    with open(cover_path, 'rb') as f:
        return f.read()


def generate_svg_cover(title, subtitle="", author="", theme=None, layout="minimal"):
    """Generate cover image from SVG template using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Warning: Playwright not installed, skipping SVG cover generation")
        return None

    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from gen_cover_svg import generate_svg_cover as gen_svg, convert_svg_to_image

    svg_path = gen_svg(title, subtitle, author, theme=theme, layout=layout)
    cover_path = "/tmp/epub_cover_svg.jpg"
    convert_svg_to_image(svg_path, cover_path)

    with open(cover_path, 'rb') as f:
        return f.read()


def create_epub(args):
    """Generate EPUB with enhanced Markdown rendering and image downloading."""
    input_dir = os.path.expanduser(args.input_dir)
    output_path = os.path.expanduser(args.output_file)

    md_files = sorted(glob.glob(os.path.join(input_dir, "*.md")))
    if not md_files:
        print(f"Error: No .md files found in {input_dir}")
        sys.exit(1)

    print(f"Generating Enhanced EPUB...")
    print(f"  Input: {input_dir} ({len(md_files)} articles)")
    print(f"  Output: {output_path}")

    # Extract title from first article if not provided
    title = args.title
    if not title:
        first_title, _, _ = parse_article(md_files[0])
        title = first_title

    book = epub.EpubBook()
    book.set_identifier(f'epub-{title.replace(" ", "-").lower()[:30]}')
    book.set_title(title)
    book.set_language(args.language)

    if args.author:
        for a in args.author.split('/'):
            book.add_author(a.strip())

    book.add_metadata('DC', 'description', f'{len(md_files)} articles')

    # Handle cover
    cover_data = None
    if args.cover:
        cover_path = os.path.expanduser(args.cover)
        if os.path.exists(cover_path):
            cover_data = compress_image(cover_path, target_width=1400, jpeg_quality=95)
            print(f"  Cover: {cover_path}")
    elif args.cover_svg:
        subtitle = args.subtitle or f"{len(md_files)} articles"
        theme = args.cover_theme if hasattr(args, 'cover_theme') else None
        layout = args.cover_layout if hasattr(args, 'cover_layout') else "minimal"
        cover_data = generate_svg_cover(title, subtitle, args.author or "", theme, layout)
        print(f"  Cover: SVG generated")
    elif args.cover_html:
        subtitle = args.subtitle or f"{len(md_files)} articles"
        cover_data = generate_html_cover(title, subtitle, args.author or "")
        print(f"  Cover: HTML generated")

    if cover_data:
        book.set_cover("cover.jpg", cover_data)

    # Process articles
    chapters = []
    toc_items = []
    spine = ['nav']
    total_img_size = 0
    total_img_count = 0

    # Check if we should split by headers (single file with ## headers)
    should_split = len(md_files) == 1
    if should_split:
        with open(md_files[0], 'r', encoding='utf-8') as f:
            full_content = f.read()

        # Extract book title from # header
        title_text, metadata, body = parse_article(md_files[0])

        # Split by ## headers
        chapter_list = split_markdown_by_headers(body)

        if len(chapter_list) > 1:
            print(f"  Splitting into {len(chapter_list)} chapters by ## headers")
        else:
            # Fallback to single chapter
            chapter_list = [(title_text, body)]
            should_split = False
    else:
        chapter_list = None

    chapter_num = 0
    for i, md_path in enumerate(md_files, 1):
        slug = Path(md_path).stem

        if should_split and chapter_list:
            # Process split chapters from single file
            for ch_title, ch_body in chapter_list:
                chapter_num += 1
                print(f"  [{chapter_num}/{len(chapter_list)}] {ch_title}")

                # Download and embed images from Markdown
                ch_body, img_count, img_size = extract_and_download_images(
                    ch_body, book, args.image_width, args.image_quality
                )
                total_img_count += img_count
                total_img_size += img_size

                if img_count > 0:
                    print(f"    → Downloaded {img_count} images ({img_size / 1024:.1f} KB)")

                # Markdown → HTML with full extensions
                md_html = markdown.markdown(
                    ch_body,
                    extensions=[
                        'extra',          # Tables, fenced code blocks, etc.
                        'codehilite',     # Syntax highlighting
                        'nl2br',          # Newline to <br>
                        'sane_lists'      # Better list handling
                    ],
                    extension_configs={
                        'codehilite': {
                            'noclasses': True,
                            'pygments_style': 'default'
                        }
                    }
                )
                md_html = fix_xhtml(md_html)

                chapter_html = build_xhtml(ch_title, "", "", md_html)

                chapter = epub.EpubHtml(
                    title=ch_title,
                    file_name=f"chapter_{chapter_num:03d}.xhtml",
                    lang=args.language
                )
                chapter.set_content(chapter_html.encode('utf-8'))

                book.add_item(chapter)
                chapters.append(chapter)
                toc_items.append(epub.Link(f"chapter_{chapter_num:03d}.xhtml", ch_title, f"ch{chapter_num}"))
                spine.append(chapter)
        else:
            # Process multiple files normally
            chapter_num += 1
            print(f"  [{chapter_num}/{len(md_files)}] {slug}")

            title_text, metadata, body = parse_article(md_path)

            # Download and embed images from Markdown
            body, img_count, img_size = extract_and_download_images(
                body, book, args.image_width, args.image_quality
            )
            total_img_count += img_count
            total_img_size += img_size

            if img_count > 0:
                print(f"    → Downloaded {img_count} images ({img_size / 1024:.1f} KB)")

            # Markdown → HTML with full extensions
            md_html = markdown.markdown(
                body,
                extensions=[
                    'extra',          # Tables, fenced code blocks, etc.
                    'codehilite',     # Syntax highlighting
                    'nl2br',          # Newline to <br>
                    'sane_lists'      # Better list handling
                ],
                extension_configs={
                    'codehilite': {
                        'noclasses': True,
                        'pygments_style': 'default'
                    }
                }
            )
            md_html = fix_xhtml(md_html)

            chapter_html = build_xhtml(title_text, metadata, "", md_html)

            chapter = epub.EpubHtml(
                title=title_text,
                file_name=f"chapter_{chapter_num:03d}.xhtml",
                lang=args.language
            )
            chapter.set_content(chapter_html.encode('utf-8'))

            book.add_item(chapter)
            chapters.append(chapter)
            toc_items.append(epub.Link(f"chapter_{chapter_num:03d}.xhtml", title_text, f"ch{chapter_num}"))
            spine.append(chapter)

    # TOC and navigation
    book.toc = toc_items
    book.spine = spine
    book.add_item(epub.EpubNcx())

    # Write EPUB
    options = {
        'epub3_pages': False,
        'epub3_landmark': False,
        'spine_direction': True
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    epub.write_epub(output_path, book, options)

    # Clean up shared Playwright browser for SVG conversion
    _close_svg_browser()

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    img_size_mb = total_img_size / (1024 * 1024)
    print(f"\n✅ Done!")
    print(f"  Output: {output_path}")
    print(f"  File size: {size_mb:.1f} MB")
    print(f"  Downloaded images: {total_img_count} ({img_size_mb:.1f} MB)")
    print(f"  Chapters: {len(chapters)}")


def main():
    parser = argparse.ArgumentParser(description='Enhanced EPUB generator with image downloading')
    parser.add_argument('input_dir', help='Directory containing Markdown files')
    parser.add_argument('output_file', help='Output EPUB file path')
    parser.add_argument('--title', help='Book title')
    parser.add_argument('--author', help='Author name(s), separate multiple with /')
    parser.add_argument('--language', default='zh', help='Language code (default: zh)')
    parser.add_argument('--cover', help='Cover image path (JPG/PNG)')
    parser.add_argument('--cover-html', action='store_true', help='Generate cover from HTML template')
    parser.add_argument('--cover-svg', action='store_true', help='Generate cover from SVG template (KDP 1600x2560)')
    parser.add_argument('--cover-theme', help='Cover theme: tech, business, design, literature, science, personal')
    parser.add_argument('--cover-layout', default='minimal', help='SVG cover layout: minimal, classic, modern (default: minimal)')
    parser.add_argument('--subtitle', help='Subtitle for cover')
    parser.add_argument('--image-quality', type=int, default=88, help='JPEG quality 1-100 (default: 88)')
    parser.add_argument('--image-width', type=int, default=1000, help='Max image width px (default: 1000)')

    args = parser.parse_args()
    create_epub(args)


if __name__ == "__main__":
    main()
