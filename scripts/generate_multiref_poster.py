#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import mimetypes
import os
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image


MODEL_ORDER = [
    ("gemini-3.1-flash-image-preview", 60),
    ("gemini-3-pro-image-preview", 90),
]


def image_part(path: Path) -> dict:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return {
        "inline_data": {
            "mime_type": mime,
            "data": base64.b64encode(path.read_bytes()).decode("utf-8"),
        }
    }


def generate(instruction: str, refs: list[Path], out: Path, prompt_out: Path | None, model_out: Path | None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 未设置")

    if prompt_out:
        prompt_out.write_text(instruction + "\n", encoding="utf-8")

    parts = [{"text": instruction}]
    parts.extend(image_part(path) for path in refs)

    last_error = None
    for model, timeout in MODEL_ORDER:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {"contents": [{"parts": parts}]}
        try:
            resp = requests.post(
                url,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                last_error = data["error"].get("message", "Unknown error")
                continue

            content_parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            for part in content_parts:
                inline = part.get("inlineData") or part.get("inline_data")
                if not inline:
                    continue
                raw = base64.b64decode(inline["data"])
                img = Image.open(BytesIO(raw)).convert("RGB")
                out.parent.mkdir(parents=True, exist_ok=True)
                img.save(out, quality=95)
                if model_out:
                    model_out.write_text(model + "\n", encoding="utf-8")
                return model

            last_error = "No image part in response"
        except Exception as exc:
            last_error = repr(exc)

    raise RuntimeError(f"Gemini 多参考图生成失败：{last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini 多参考图海报生成")
    parser.add_argument("--instruction", required=True, help="给 Gemini 的任务描述")
    parser.add_argument("--ref", action="append", required=True, help="参考图路径，可重复多次")
    parser.add_argument("--out", required=True, help="输出图片路径")
    parser.add_argument("--prompt-out", help="保存最终 prompt 的路径")
    parser.add_argument("--model-out", help="保存实际使用模型的路径")
    args = parser.parse_args()

    refs = [Path(p).expanduser().resolve() for p in args.ref]
    for path in refs:
        if not path.exists():
            raise FileNotFoundError(f"Missing ref image: {path}")

    model = generate(
        instruction=args.instruction,
        refs=refs,
        out=Path(args.out).expanduser().resolve(),
        prompt_out=Path(args.prompt_out).expanduser().resolve() if args.prompt_out else None,
        model_out=Path(args.model_out).expanduser().resolve() if args.model_out else None,
    )
    print(f"OK: {args.out}")
    print(f"MODEL: {model}")


if __name__ == "__main__":
    main()
