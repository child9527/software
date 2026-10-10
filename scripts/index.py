#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

from github import Github, Auth

from renderer import render
from sections import (
    section_software_list,
    section_copy_cards,
    section_copy_cards_wide,
)


# ============================================================
# 配置
# ============================================================

# 镜像前缀
MIRRORS = [
    ("GH-Proxy", "https://gh-proxy.com/"),
    ("GH-Fast", "https://ghfast.top/"),
]

# 音源目录
LX_SOURCES_DIR = os.path.join("lxSources", "guoyue2010")

# 输出文件
OUTPUT = "index.html"


# ============================================================
# 工具函数
# ============================================================

def format_size(size):
    """把字节数格式化成人类可读的大小"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    else:
        return f"{size/1024/1024:.1f} MB"


# ============================================================
# 数据获取
# ============================================================

def fetch_release_items():
    """
    从当前仓库的 Releases 拿软件列表。
    每个 Release 的 tag 形如 {rawname}-latest。
    """
    token = os.getenv("GITHUB_TOKEN")
    auth = Auth.Token(token)
    g = Github(auth=auth)

    repo_name = os.getenv("GITHUB_REPOSITORY", "child9527/software")
    repo = g.get_repo(repo_name)

    # 读取 targets.json
    with open("task/targets.json", "r", encoding="utf-8") as f:
        targets = json.load(f)

    # 建立 rawname -> target 的映射，大小写不敏感
    target_map = {}
    for t in targets:
        rn = t.get("rawname", t["name"])
        target_map[rn.lower()] = t

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

        # 从 tag 反推 rawname：{rawname}-latest -> rawname
        raw_name = tag[:-len("-latest")]

        # 用 rawname 去匹配 targets.json
        t = target_map.get(raw_name.lower())
        if t is None:
            print(f"⚠️ 未找到匹配的 targets.json 项：{tag}，已跳过")
            continue

        icon_url = t.get("icon")
        upstream_repo_name = t["repo"]
        display_name = t["name"]
        item_type = t.get("type", "其他")
        description = "暂无简介"

        overview = t.get("overview")
        if overview and str(overview).strip():
            description = str(overview).strip()

        # 拼接原始下载链接
        raw_url = (
            f"https://github.com/{repo_name}/releases/download/"
            f"{quote(raw_name)}-latest/{asset.name}"
        )

        # 从上游仓库拿最新版本号
        upstream_repo = g.get_repo(upstream_repo_name)
        upstream_release = upstream_repo.get_latest_release()
        version = upstream_release.tag_name

        items.append({
            "name": display_name,
            "version": version,
            "url": raw_url,
            "file_size": asset.size,
            "file_size_text": format_size(asset.size),
            "icon": icon_url,
            "type": item_type,
            "description": description,
            "mirrors": [(m[0], f"{m[1]}{raw_url}") for m in MIRRORS],
        })

    return items


def fetch_lx_sources():
    """
    扫描 lxSources/guoyue2010 目录下的所有 .js 文件。
    返回 [{name, url_literal}]，url_literal 已经过 json.dumps，可直接塞进 JS。
    """
    if not os.path.exists(LX_SOURCES_DIR):
        print(f"⚠️ 未找到音源目录: {LX_SOURCES_DIR}")
        return []

    repo_name = os.getenv("GITHUB_REPOSITORY", "child9527/software")
    sources = []

    for fname in os.listdir(LX_SOURCES_DIR):
        if not fname.endswith(".js"):
            continue

        # 对文件名做 URL 编码（防中文/空格）
        encoded_fname = quote(fname)

        raw_url = (
            f"https://raw.githubusercontent.com/{repo_name}/main/"
            f"lxSources/guoyue2010/{encoded_fname}"
        )
        gh_proxy_url = f"https://gh-proxy.com/{raw_url}"

        # 展示名去掉 .js 后缀
        display_name = fname[:-3]

        sources.append({
            "name": display_name,
            "url_literal": json.dumps(gh_proxy_url, ensure_ascii=False),
        })

    # 按文件名长度排序
    sources.sort(key=lambda x: len(x["name"]))
    return sources


# ============================================================
# 组装 sections
# ============================================================

def build_sections():
    """
    组装所有板块。

    以后新增板块，只改这里：
        sections.append(section_xxx("板块标题", 数据))
    """
    sections = []

    # 板块 1：软件自动更新列表
    items = fetch_release_items()
    sections.append(section_software_list("🚀 软件自动更新列表", items))

    # 板块 2：洛雪音乐音源
    lx_sources = fetch_lx_sources()
    sections.append(section_copy_cards("🎵 洛雪音乐音源", lx_sources))

    # 板块 3：复制规则（暂时注释，以后要加时打开）
    # 示例：
    # with open("scripts/extension_js.txt", "r", encoding="utf-8") as f:
    #     js_text = f.read()
    # sections.append(section_copy_cards_wide("📋 规则及配置", [
    #     {
    #         "name": "Clash Verge Rev全局扩展覆写脚本",
    #         "js_var": "EXTENSION_JS_TEXT",
    #         "content_literal": json.dumps(js_text, ensure_ascii=False),
    #     },
    # ]))

    return sections


# ============================================================
# 主入口
# ============================================================

def main():
    bj_tz = timezone(timedelta(hours=8))
    now = datetime.now(bj_tz).strftime("%Y-%m-%d %H:%M:%S")

    sections = build_sections()

    html = render(
    "base.html.j2",
    sections=sections,
    now=now,
    page_title="软件中心",
    )

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html 生成成功！共 {len(sections)} 个板块。")


if __name__ == "__main__":
    main()
