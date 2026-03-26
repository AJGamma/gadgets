#!/usr/bin/env python3
"""
arxiv_downloader.py
用法: python arxiv_downloader.py links.txt [-o output_dir] [-d delay]
"""

import re
import sys
import time
import argparse
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ── 工具函数 ────────────────────────────────────────────────────────────────

def to_snake_case(title: str) -> str:
    """将论文标题转换为 snake_case 文件名。"""
    # 规范化 unicode（把 é → e 之类的带音符字母转为 ASCII）
    title = unicodedata.normalize("NFKD", title)
    title = title.encode("ascii", "ignore").decode("ascii")
    # 转小写
    title = title.lower()
    # 把非字母数字字符（含空格、连字符、标点）统一换成下划线
    title = re.sub(r"[^a-z0-9]+", "_", title)
    # 去掉首尾下划线并压缩连续下划线
    title = re.sub(r"_+", "_", title).strip("_")
    return title


def normalize_arxiv_id(url_or_id: str) -> str | None:
    """
    从各种形式的 arxiv 输入中提取论文 ID。
    支持:
      2501.12345          纯 ID
      2501.12345v2        带版本
      https://arxiv.org/abs/2501.12345
      https://arxiv.org/pdf/2501.12345
    """
    url_or_id = url_or_id.strip()
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", url_or_id)
    return match.group(1) if match else None


def fetch_title(arxiv_id: str, session: requests.Session) -> str:
    """从 abs 页面抓取论文标题。"""
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"
    resp = session.get(abs_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    h1 = soup.find("h1", class_="title mathjax")
    if not h1:
        raise ValueError(f"找不到标题元素，请检查页面结构：{abs_url}")
    # 去掉 "Title:" descriptor span
    for span in h1.find_all("span", class_="descriptor"):
        span.decompose()
    return h1.get_text(separator=" ", strip=True)


def download_pdf(arxiv_id: str, dest: Path, session: requests.Session) -> None:
    """下载 PDF 并写入 dest。支持流式下载以节省内存。"""
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    with session.get(pdf_url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):  # 1 MB
                f.write(chunk)


# ── 主流程 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="批量下载 arXiv PDF 并以 snake_case 命名")
    parser.add_argument("links_file", help="包含 arXiv 链接或 ID 的文本文件（每行一个）")
    parser.add_argument("-o", "--output", default=".", help="PDF 保存目录（默认当前目录）")
    parser.add_argument("-d", "--delay", type=float, default=3.0,
                        help="每次请求间隔秒数，避免被限速（默认 3 秒）")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    links_file = Path(args.links_file)
    if not links_file.exists():
        print(f"[错误] 文件不存在: {links_file}", file=sys.stderr)
        sys.exit(1)

    lines = [l.strip() for l in links_file.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; arxiv-downloader/1.0)"
    })

    ok, fail = 0, 0

    for i, line in enumerate(lines, 1):
        arxiv_id = normalize_arxiv_id(line)
        if not arxiv_id:
            print(f"[{i}/{len(lines)}] ⚠  无法解析 ID，跳过: {line!r}")
            fail += 1
            continue

        print(f"[{i}/{len(lines)}] 处理 {arxiv_id} …", end=" ", flush=True)

        try:
            title = fetch_title(arxiv_id, session)
            snake = to_snake_case(title)
            dest = output_dir / f"{snake}.pdf"

            # 若同名文件已存在则跳过
            if dest.exists():
                print(f"已存在，跳过 → {dest.name}")
                ok += 1
                continue

            download_pdf(arxiv_id, dest, session)
            print(f"✓ → {dest.name}")
            ok += 1

        except requests.HTTPError as e:
            print(f"✗ HTTP 错误: {e}")
            fail += 1
        except Exception as e:
            print(f"✗ {e}")
            fail += 1

        # 礼貌性延迟，避免对 arXiv 造成压力
        if i < len(lines):
            time.sleep(args.delay)

    print(f"\n完成：{ok} 成功，{fail} 失败。文件保存于 {output_dir.resolve()}")


if __name__ == "__main__":
    main()
