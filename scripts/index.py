#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
from github import Github, Auth

OUTPUT = "index.html"

def fetch_release_items():
    """从当前仓库的 Releases 获取所有真实下载链接，并替换为 Pages 域名"""
    token = os.getenv("GITHUB_TOKEN")
    auth = Auth.Token(token)
    g = Github(auth=auth)

    repo_name = os.getenv("GITHUB_REPOSITORY")
    repo = g.get_repo(repo_name)

    releases = list(repo.get_releases())
    items = []

    for rel in releases:
        tag = rel.tag_name

        if not tag.endswith("-latest"):
            continue

        assets = list(rel.get_assets())
        if not assets:
            continue

        asset = assets[0]
        raw_url = asset.browser_download_url

        # ⭐ 关键替换：把 github.com 换成 github.io
        download_url = raw_url.replace(
            f"https://github.com/{repo_name}",
            f"https://{repo_name.split('/')[0]}.github.io/{repo_name.split('/')[1]}"
        )

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
<title>软件 Releases 自动导航</title>
<style>
    body {{
        font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
        background-color: #1a1a1a;
        color: #e0e0e0;
        padding: 20px;
    }}
    .container {{
        max-width: 900px;
        margin: auto;
    }}
    h2 {{
        color: #ff4757;
        border-bottom: 2px solid #ff4757;
        padding-bottom: 8px;
    }}
    .section {{
        background: #2d2d2d;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }}
    .data-row {{
        display: grid;
        grid-template-columns: 160px 1fr 90px;
        padding: 10px 0;
        border-bottom: 1px solid #444;
    }}
    .data-value {{
        color: #5dade2;
        cursor: pointer;
        word-break: break-all;
    }}
    .download-btn {{
        background: #3498db;
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        text-align: center;
        cursor: pointer;
    }}
</style>
</head>
<body>

<div class="container">
<h2>软件 Releases 自动导航</h2>
<div class="section">
"""

    for item in items:
        html += f"""
    <div class="data-row">
        <span>{item['name']}</span>
        <span class="data-value" onclick="copy(this)">{item['url']}</span>
        <span class="download-btn" onclick="window.open('{item['url']}', '_blank')">下载</span>
    </div>
"""

    html += f"""
</div>
<div style="margin-top:20px;color:#888;font-size:0.8rem;">
    自动生成时间：{now}
</div>
</div>

<script>
function copy(el) {{
    const text = el.innerText;
    
    navigator.clipboard.writeText(text).then(() => {{
        // 复制成功后的视觉反馈
        el.style.color = "#2ecc71";  // 绿色
        el.style.fontWeight = "bold";

        setTimeout(() => {{
            el.style.color = "#5dade2";  // 恢复原色
            el.style.fontWeight = "normal";
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
