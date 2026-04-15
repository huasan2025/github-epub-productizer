#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser(description="把 HTML 商品图截图成 PNG")
    parser.add_argument("--html", default="Software-Engineering-at-Google-product-poster.html", help="输入 HTML 路径")
    parser.add_argument("--out", default="Software-Engineering-at-Google-product-poster-html.png", help="输出 PNG 路径")
    args = parser.parse_args()

    html_path = Path(args.html).expanduser().resolve()
    png_path = Path(args.out).expanduser().resolve()

    if not html_path.exists():
        raise FileNotFoundError(f"Missing HTML poster: {html_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 2200}, device_scale_factor=1)
        page.goto(html_path.as_uri(), wait_until="networkidle")
        poster = page.locator("#poster")
        png_path.parent.mkdir(parents=True, exist_ok=True)
        poster.screenshot(path=str(png_path))
        browser.close()

    print(f"OK: {png_path}")


if __name__ == "__main__":
    main()
