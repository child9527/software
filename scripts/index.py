import os
import json
from github import Github, Auth
from datetime import datetime

# 镜像前缀
MIRRORS = [
    ("GH-Proxy", "https://gh-proxy.com/"),
    ("Wget.LA", "https://wget.la/"),
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

    # 读取 targets.json（task目录）
    with open("task/targets.json", "r", encoding="utf-8") as f:
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

        # 使用 Release 的 name/title 来匹配 targets.json（最稳）
        release_name = rel.title or rel.name or ""

        icon_url = None
        upstream_repo_name = None

        for t in targets:
            if t["name"].lower() == release_name.lower():
                icon_url = t.get("icon")
                upstream_repo_name = t["repo"]
                break

        # 如果匹配不到，跳过（避免 None 报错）
        if upstream_repo_name is None:
            print(f"⚠ 未找到匹配的 targets.json 项：{release_name}，已跳过")
            continue

        # 获取上游仓库简介
        upstream_repo = g.get_repo(upstream_repo_name)
        description = upstream_repo.description or "暂无简介"

        # 从 Release body 中提取版本号
        upstream_release = upstream_repo.get_latest_release()
        version = upstream_release.tag_name

        # 添加到 items
        items.append({
            "name": release_name,
            "version": version,
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
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>软件中心 · Child9527</title>
<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #1e1e1e;
    color: #e0e0e0;
}

/* 顶部导航栏 */
.navbar {
    width: 100%;
    background: #2b2b2b;
    border-bottom: 2px solid #4aa3ff;
    padding: 12px 20px;
    display: flex;
    gap: 20px;
    align-items: center;
    box-shadow: 0 0 12px rgba(74,163,255,0.3);
}

.navbar a {
    color: #e0e0e0;
    text-decoration: none;
    font-size: 16px;
    padding: 6px 10px;
    border-radius: 6px;
    transition: 0.2s;
}

.navbar a:hover {
    background: #4aa3ff;
    color: #000;
}

/* 内容区块 */
.section {
    max-width: 1000px;
    margin: 40px auto;
    padding: 0 20px;
}

/* 卡片 */
.card {
    background: #2b2b2b;
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #4aa3ff;
    box-shadow: 0 0 12px rgba(74,163,255,0.4);
    margin-bottom: 20px;
    display: flex;
    align-items: flex-start;
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
    color: #ffffff;
}

.version {
    color: #b0b0b0;
}

.size {
    color: #999999;
}

.desc {
    margin: 8px 0;
    color: #cccccc;
}

.btn {
    display: inline-block;
    margin: 5px 5px 0 0;
    padding: 8px 12px;
    background: #3a7bd5;
    color: white;
    border-radius: 5px;
    text-decoration: none;
}

.btn:hover {
    background: #2f6bb8;
}

/* 底部 */
.footer {
    text-align: center;
    padding: 20px;
    color: #888888;
    margin-top: 40px;
}
</style>
</head>

<body>

<!-- 导航栏 -->
<div class="navbar">
    <a href="https://child9527.github.io/">首页</a>
    <a href="https://child9527.github.io/tvbox/">TVbox订阅</a>
    <a href="https://child9527.github.io/about/">关于本站</a>
</div>

<!-- 内容区块 -->
<div class="section">
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
