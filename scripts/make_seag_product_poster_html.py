#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


HTML = dedent(
    """\
    <!doctype html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Software Engineering at Google 商品图</title>
      <style>
        :root {
          --bg-1: #09172d;
          --bg-2: #0f2c56;
          --bg-3: #123d73;
          --cyan: #7de3ff;
          --blue: #2f8fff;
          --yellow: #ffd867;
          --text: #f8fbff;
          --muted: #bbd4ea;
          --panel: rgba(8, 25, 54, 0.88);
          --white-panel: rgba(255, 255, 255, 0.98);
        }

        * { box-sizing: border-box; }
        html, body {
          margin: 0;
          width: 1536px;
          height: 2048px;
          font-family: "Hiragino Sans GB", "PingFang SC", "Microsoft YaHei", sans-serif;
          background: radial-gradient(circle at 15% 15%, rgba(111, 227, 255, 0.28), transparent 22%),
                      radial-gradient(circle at 85% 18%, rgba(47, 143, 255, 0.22), transparent 18%),
                      linear-gradient(160deg, var(--bg-1) 0%, var(--bg-2) 54%, var(--bg-3) 100%);
          overflow: hidden;
        }

        body::before,
        body::after {
          content: "";
          position: absolute;
          inset: 0;
          pointer-events: none;
        }

        body::before {
          background-image:
            linear-gradient(rgba(125, 227, 255, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(125, 227, 255, 0.08) 1px, transparent 1px);
          background-size: 64px 64px;
          mask-image: linear-gradient(to bottom, rgba(0,0,0,0.45), rgba(0,0,0,0.05));
        }

        body::after {
          background:
            linear-gradient(135deg, rgba(255,255,255,0.1), transparent 16%),
            radial-gradient(circle at 82% 72%, rgba(125, 227, 255, 0.18), transparent 18%);
        }

        .frame {
          width: 100%;
          height: 100%;
          padding: 110px 76px;
          display: grid;
          grid-template-columns: 654px 1fr;
          gap: 40px;
        }

        .cover-panel,
        .info-panel {
          border-radius: 40px;
          position: relative;
          box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
        }

        .cover-panel {
          background: var(--white-panel);
          padding: 34px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .cover-panel img {
          width: 100%;
          height: auto;
          display: block;
          border-radius: 22px;
          box-shadow: 0 14px 34px rgba(0, 0, 0, 0.12);
        }

        .info-panel {
          background: linear-gradient(180deg, rgba(8, 26, 58, 0.93), rgba(8, 25, 54, 0.87));
          border: 2px solid rgba(132, 209, 255, 0.22);
          padding: 54px 46px 42px;
          color: var(--text);
          display: flex;
          flex-direction: column;
        }

        .title {
          font-size: 80px;
          font-weight: 900;
          line-height: 1.06;
          letter-spacing: -1px;
          margin: 0;
        }

        .subtitle {
          margin-top: 18px;
          font-size: 34px;
          line-height: 1.2;
          color: #a8d8ff;
          font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
        }

        .badges {
          margin-top: 34px;
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
        }

        .badge {
          border-radius: 18px;
          background: linear-gradient(180deg, #3295ff, #216ee3);
          color: white;
          padding: 14px 22px;
          font-size: 31px;
          font-weight: 800;
          line-height: 1;
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.2);
        }

        .points {
          margin-top: 34px;
          display: grid;
          gap: 28px;
        }

        .point {
          border-radius: 30px;
          background: rgba(10, 35, 79, 0.95);
          border: 1px solid rgba(125, 227, 255, 0.18);
          padding: 28px 28px 24px 30px;
          position: relative;
          overflow: hidden;
        }

        .point::before {
          content: "";
          position: absolute;
          left: 0;
          top: 28px;
          bottom: 28px;
          width: 14px;
          border-radius: 0 10px 10px 0;
          background: linear-gradient(180deg, #7de3ff, #2f8fff);
        }

        .point h2 {
          margin: 0 0 16px 26px;
          font-size: 56px;
          line-height: 1.12;
          font-weight: 900;
          color: white;
        }

        .point p {
          margin: 0 0 0 26px;
          font-size: 31px;
          line-height: 1.36;
          color: var(--muted);
        }

        .quote {
          margin-top: 32px;
          border-radius: 28px;
          background: linear-gradient(180deg, #ffe9a5, #ffd86b);
          color: #1d3769;
          padding: 28px 30px;
          font-size: 47px;
          line-height: 1.18;
          font-weight: 900;
          box-shadow: 0 14px 24px rgba(0, 0, 0, 0.14);
        }

        .footer {
          margin-top: auto;
          border-radius: 26px;
          background: rgba(255, 255, 255, 0.98);
          color: #163462;
          padding: 24px 26px 22px;
        }

        .footer strong {
          display: block;
          font-size: 40px;
          line-height: 1.2;
          font-weight: 900;
        }

        .footer span {
          display: block;
          margin-top: 8px;
          font-size: 29px;
          line-height: 1.28;
          color: #5e7290;
        }
      </style>
    </head>
    <body>
      <main class="frame">
        <section class="cover-panel">
          <img src="./封面图.png" alt="Software Engineering at Google 封面" />
        </section>

        <section class="info-panel">
          <h1 class="title">Google 软件工程经典</h1>
          <div class="subtitle">Software Engineering at Google</div>

          <div class="badges">
            <div class="badge">中英对照</div>
            <div class="badge">EPUB 格式</div>
            <div class="badge">适合阅读器</div>
          </div>

          <div class="points">
            <article class="point">
              <h2>中英对照 EPUB</h2>
              <p>微信读书、Apple Books、Calibre 直接可读</p>
            </article>

            <article class="point">
              <h2>协作 评审 测试<br />一次讲透</h2>
              <p>不是碎片技巧，是一套完整的软件工程框架</p>
            </article>

            <article class="point">
              <h2>开发者 / 技术负责人<br />都值得看</h2>
              <p>越早建立工程视角，越少在项目里反复踩坑</p>
            </article>
          </div>

          <div class="quote">好代码只是起点<br />真正拉开差距的是软件工程</div>

          <div class="footer">
            <strong>整理好的 EPUB 电子书，拍下发货</strong>
            <span>虚拟资料按描述发出，不退不换</span>
          </div>
        </section>
      </main>
    </body>
    </html>
    """
)


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 HTML 商品图模板")
    parser.add_argument("--cover", default="封面图.png", help="封面图相对路径，写入 HTML")
    parser.add_argument("--out", default="Software-Engineering-at-Google-product-poster.html", help="输出 HTML 路径")
    args = parser.parse_args()

    html = HTML.replace("./封面图.png", f"./{Path(args.cover).name}")
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
