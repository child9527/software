import os
import json
from github import Github, Auth
from datetime import datetime

# 镜像前缀
MIRRORS = [
    ("KSX 镜像", "https://web.ksx.qzz.io/"),
    ("GH-Proxy Com", "https://gh-proxy.com/"),
    ("Wget LA", "https://wget.la/"),
]

def format_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    else:
        return f"{size/1024/1024:.1f} MB"

def fetch_release_items():
    token = os.getenv("GITHUB_TOKEN")
    auth = Auth.Token(token)
    g = Github(auth=auth)

    repo_name = os.getenv("GITHUB_REPOSITORY")
    repo = g.get_repo(repo_name)

    # 读取 targets.json
    with open("./targets.json", "r", encoding="utf-8") as f:
        targets = json.load(f)

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

        # 找到对应软件的 icon 和上游 repo
        icon_url = None
        upstream_repo_name = None
        for t in targets:
            if t["name"].lower() in tag.lower():
                icon_url = t.get("icon")
                upstream_repo_name = t["repo"]
                break

        # 获取上游仓库简介
        upstream_repo = g.get_repo(upstream_repo_name)
        description = upstream_repo.description or "暂无简介"

        items.append({
            "name": rel.title or rel.name or tag.replace("-latest", ""),
            "version": tag.replace("-latest", ""),
            "url": raw_url,
            "file_size": asset.size,
            "icon": icon_url,
            "description": description,
            "mirrors": [(m[0], f"{m[1]}{raw_url}") for m in MIRRORS]
        })

    return items

def generate_html(items):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>软件自动更新列表</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: #f4f6f7;
    padding: 20px;
}
.container {
    max-width: 900px;
    margin: auto;
}
.card {
    background: white;
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 10px;
    display: flex;
    align-items: flex-start;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
.icon {
    width: 64px;
    height: 64px;
    border-radius: 12px;
    margin-right: 15px;
}
.name {
    font-size: 20px;
    font-weight: bold;
}
.version {
    color: #666;
}
.size {
    color: #999;
}
.desc {
    margin: 8px 0;
    color: #555;
}
.btn {
    display: inline-block;
    margin: 5px 5px 0 0;
    padding: 8px 12px;
    background: #3498db;
    color: white;
    border-radius: 5px;
    text-decoration: none;
}
.btn:hover {
    background: #2980b9;
}
.footer {
    margin-top: 20px;
    text-align: center;
    color: #888;
}
</style>
</head>
<body>
<div class="container">
<h2>软件自动更新列表</h2>
"""

    for item in items:
        icon_html = f'<img class="icon" src="{item["icon"]}">' if item["icon"] else ""

        html += f"""
<div class="card">
    {icon_html}
    <div>
        <div class="name">{item['name']}</div>
        <div class="version">版本号：{item['version']}</div>
        <div class="size">文件大小：{format_size(item['file_size'])}</div>
        <div class="desc">{item['description']}</div>

        <a class="btn" href="{item['url']}">原始下载</a>
"""

        for mirror_name, mirror_url in item["mirrors"]:
            html += f'<a class="btn" href="{mirror_url}">{mirror_name}</a>'

        html += "</div></div>"

    html += f"""
<div class="footer">
    自动生成时间：{now}
</div>
</div>
</body>
</html>
"""

    return html

if __name__ == "__main__":
    items = fetch_release_items()
    html = generate_html(items)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
