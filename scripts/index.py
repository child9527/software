#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime

OUTPUT = "index.html"

def load_targets():
    with open("targets.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_html():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    targets = load_targets()

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

    # 自动生成软件列表
    for item in targets:
        name = item["name"]

        # Release 标签规则：软件名转小写并用 -latest
        release_tag = name.lower().replace(" ", "-") + "-latest"

        # 明文地址（你希望中间显示这个）
        plain_url = f"https://github.com/child9527/software/releases/download/{release_tag}/"

        # 下载按钮跳转地址
        download_url = plain_url

        html += f"""
    <div class="data-row">
        <span class="data-label">{name}</span>
        <span class="data-value" onclick="copy(this)">{plain_url}</span>
        <span class="download-btn" onclick="window.open('{download_url}', '_blank')">下载</span>
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
    generate_html()
