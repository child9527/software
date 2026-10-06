import os
import json
from github import Github, Auth
from datetime import datetime, timezone, timedelta

# 镜像前缀
MIRRORS = [
    ("GH-Proxy", "https://gh-proxy.com/"),
    ("GH-Fast", "https://ghfast.top/"),
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
            print(f"?? 未找到匹配的 targets.json 项：{release_name}，已跳过")
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


def fetch_lx_sources():
    """扫描本地 lxSources/guoyue2010 目录下的所有 .js 音源文件，仅生成 gh-proxy 镜像链接"""
    target_dir = os.path.join("lxSources", "guoyue2010")
    if not os.path.exists(target_dir):
        print(f"?? 未找到音源目录: {target_dir}")
        return []

    repo_name = os.getenv("GITHUB_REPOSITORY", "child9527/software")
    sources = []

    for fname in os.listdir(target_dir):
        if fname.endswith(".js"):
            raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/lxSources/guoyue2010/{fname}"
            gh_proxy_url = f"https://gh-proxy.com/{raw_url}"
            name = fname[:-3]  # 去掉末尾的 .js

            sources.append({
                "name": name,
                "gh_proxy_url": gh_proxy_url
            })

    # 按文件名长度排序
    sources.sort(key=lambda x: len(x["name"]))
    return sources


def generate_html(items, lx_sources):
    bj_tz = timezone(timedelta(hours=8))
    now = datetime.now(bj_tz).strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>软件中心 · Child9527</title>
<style>
body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #1e1e1e;
    color: #e0e0e0;
}}

/* 顶部导航栏 */
.navbar {{
    width: 100%;
    background: #2b2b2b;
    border-bottom: 2px solid #4aa3ff;
    padding: 12px 20px;
    display: flex;
    gap: 20px;
    align-items: center;
    box-shadow: 0 0 12px rgba(74,163,255,0.3);
}}

.navbar a {{
    color: #e0e0e0;
    text-decoration: none;
    font-size: 16px;
    padding: 6px 10px;
    border-radius: 6px;
    transition: 0.2s;
}}

.navbar a:hover {{
    background: #4aa3ff;
    color: #000;
}}

/* 内容区块 */
.section {{
    max-width: 1000px;
    margin: 40px auto;
    padding: 0 20px;
}}

.section-title {{
    color: #4aa3ff;
    font-size: 1.3rem;
    margin: 30px 0 15px 0;
    border-left: 4px solid #4aa3ff;
    padding-left: 10px;
}}

/* 软件卡片 */
.card {{
    background: #2b2b2b;
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #4aa3ff;
    box-shadow: 0 0 12px rgba(74,163,255,0.4);
    margin-bottom: 20px;
    display: flex;
    align-items: flex-start;
}}

.icon {{
    width: 64px;
    height: 64px;
    border-radius: 12px;
    margin-right: 15px;
}}

.name {{
    font-size: 20px;
    font-weight: bold;
    color: #ffffff;
}}

.version {{
    color: #b0b0b0;
}}

.size {{
    color: #999999;
}}

.desc {{
    margin: 8px 0;
    color: #cccccc;
}}

.btn {{
    display: inline-block;
    margin: 5px 5px 0 0;
    padding: 8px 12px;
    background: #3a7bd5;
    color: white;
    border-radius: 5px;
    text-decoration: none;
}}

.btn:hover {{
    background: #2f6bb8;
}}

/* 洛雪音源紧凑卡片网格 */
.compact-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
    margin-bottom: 30px;
}}

.source-card {{
    background: #2b2b2b;
    border: 1px solid #4aa3ff;
    box-shadow: 0 0 8px rgba(74,163,255,0.3);
    border-radius: 10px;
    padding: 12px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
}}

.source-name {{
    color: #ffffff;
    font-size: 0.95rem;
    font-weight: bold;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.copy-btn {{
    font-size: 0.85rem;
    padding: 6px 12px;
    background: #3a7bd5;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
}}

.copy-btn:hover {{
    background: #2f6bb8;
}}

/* Toast 提示浮窗 */
.toast {{
    position: fixed;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(74, 163, 255, 0.95);
    color: #000;
    font-weight: bold;
    padding: 10px 20px;
    border-radius: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    display: none;
    z-index: 1000;
}}

/* 底部 */
.footer {{
    text-align: center;
    padding: 20px;
    color: #888888;
    margin-top: 40px;
}}
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
<h2>软件中心</h2>

<!-- 1. 软件列表 -->
<div class="section-title">软件自动更新列表</div>
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

    # 2. 洛雪音乐音源区块
    html += """
<!-- 2. 洛雪音乐音源 -->
<div class="section-title">洛雪音乐音源</div>
<div class="compact-grid">
"""

    for src in lx_sources:
        html += f"""
    <div class="source-card">
        <div class="source-name">{src['name']}</div>
        <button class="copy-btn" onclick="copyUrl(this, '{src['gh_proxy_url']}')">复制链接</button>
    </div>
"""

    html += f"""
</div>

<div class="footer">
    自动生成时间：{now}
</div>
</div>

<div id="toast" class="toast">链接已成功复制到剪贴板！</div>

<script>
function copyUrl(btn, url) {{
    navigator.clipboard.writeText(url).then(() => {{
        showToast("已复制：" + url);
        const originalText = btn.innerText;
        btn.innerText = "已复制";
        btn.style.background = "#28a745";
        setTimeout(() => {{
            btn.innerText = originalText;
            btn.style.background = "#3a7bd5";
        }}, 2000);
    }}).catch(err => {{
        console.error("复制失败:", err);
    }});
}}

function showToast(msg) {{
    const toast = document.getElementById("toast");
    toast.innerText = msg;
    toast.style.display = "block";
    setTimeout(() => {{
        toast.style.display = "none";
    }}, 2000);
}}
</script>

</body>
</html>
"""

    return html


if __name__ == "__main__":
    items = fetch_release_items()
    lx_sources = fetch_lx_sources()
    html = generate_html(items, lx_sources)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html 生成成功！")
