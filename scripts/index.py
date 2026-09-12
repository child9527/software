#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
from github import Github, Auth

OUTPUT = "index.html"

def fetch_release_items():
    """从当前仓库的 Releases 获取所有真实下载链接"""
    token = os.getenv("GITHUB_TOKEN")
    auth = Auth.Token(token)
    g = Github(auth=auth)

    repo_name = os.getenv("GITHUB_REPOSITORY")
    repo = g.get_repo(repo_name)

    releases = list(repo.get_releases())
    items = []

    for rel in releases:
        tag = rel.tag_name

        # 只处理你自动同步生成的 *-latest
        if not tag.endswith("-latest"):
            continue

        assets = list(rel.get_assets())
        if not assets:
            continue

        asset = assets[0]  # 每个 release 只有一个文件
        download_url = asset.browser_download_url

        # Release 名作为软件名
        name = rel.title or rel.name or tag.replace("-latest", "")

        items.append({
            "name": name,
            "url": download_url,
        })

    return items


def generate_html(items):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>软件 Releases 自动导航 - child9527</title>

<style>
    body {{
        font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
        background-color: #1a1a1a;
        color: #e0e0e0;
        margin: 0;
        padding: 20px;
        line-height: 1.6;
    }}

    .container {{
        max-width: 900px;
        margin: 0 auto;
    }}

    h2 {{
        color: #ff4757;
        border-bottom: 2px solid #ff4757;
        padding-bottom: 8px;
        margin-top: 30px;
        font-size: 1.5rem;
    }}

    .section {{
        background: #2d2d2d;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }}

    .data-row {{
        display: grid;
        grid-template-columns: 160px 1fr 90px;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #444;
    }}

    .data-label {{
        font-size: 0.95rem;
        color: #ddd;
        font-weight: 500;
    }}

    .data-value {{
        font-size: 0.9rem;
        color: #5dade2;
        cursor: pointer;
        word-break: break-all;
    }}

    .data-value:hover {{
        color: #7fc8ff;
    }}

    .download-btn {{
        background: #3498db;
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        text-align: center;
        cursor: pointer;
        font-size: 0.85rem;
        transition: 0.2s;
    }}

    .download-btn:hover {{
        background: #5dade2;
    }}

    .footer {{
        margin-top: 20px;
        font-size: 0.8rem;
        color: #888;
    }}
</style>

</head>
<body>

<div class="container">

<h2>软件 Releases 自动导航</h2>

<div class="section">
"""

    for item in items:
        name = item["name"]
        url = item["url"]

        html += f"""
    <div class="data-row">
        <span class="data-label">{name}</span>
        <span class="data-value" onclick="copy(this)">{url}</span>
        <span class="download-btn" onclick="window.open('{url}', '_blank')">下载</span>
    </div>
"""

    html += f"""
</div>

<div class="footer">
    自动生成时间：{now}
</div>

</div>

<script>
function copy(el) {{
    const text = el.innerText;
    navigator.clipboard.writeText(text).then(() => {{
        el.style.color = "#2ecc71";
        setTimeout(() => {{
            el.style.color = "#5dade2";
        }}, 1200);
    }});
}}
</script>

</body>
</html>
"""

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html 已生成 → {OUTPUT}")


if __name__ == "__main__":
    items = fetch_release_items()
    generate_html(items)
