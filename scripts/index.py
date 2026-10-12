#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
from typing import Optional
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

from github import Github, Auth

from renderer import render
from sections import (
    section_software_list,
    section_copy_cards_grouped,
)


# ============================================================
# 配置
# ============================================================

MIRRORS = [
    ("GH-Proxy", "https://gh-proxy.com/"),
    ("GH-Fast", "https://ghfast.top/"),
]

GH_PROXY = "https://gh-proxy.com/"

# 音源目录
GUOYUE_DIR = os.path.join("lxSources", "guoyue2010")
PDONE_DIR = os.path.join("lxSources", "pdone")
PDONE_UPSTREAM = "pdone/lx-music-source"

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


def parse_js_name(content: str) -> Optional[str]:
    """从 JS 文件头解析 @name"""
    m = re.search(r"@name\s+(.+)", content)
    return m.group(1).strip() if m else None


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

    with open("task/targets.json", "r", encoding="utf-8") as f:
        targets = json.load(f)

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
        raw_name = tag[:-len("-latest")]

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

        raw_url = (
            f"https://github.com/{repo_name}/releases/download/"
            f"{quote(raw_name)}-latest/{asset.name}"
        )

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


def fetch_guoyue2010_sources():
    """扫描 lxSources/guoyue2010 下所有 .js，type=guoyue2010"""
    if not os.path.exists(GUOYUE_DIR):
        print(f"⚠️ 未找到音源目录: {GUOYUE_DIR}")
        return []

    repo_name = os.getenv("GITHUB_REPOSITORY", "child9527/software")
    sources = []

    for fname in os.listdir(GUOYUE_DIR):
        if not fname.endswith(".js"):
            continue

        encoded_fname = quote(fname)
        raw_url = (
            f"https://raw.githubusercontent.com/{repo_name}/main/"
            f"lxSources/guoyue2010/{encoded_fname}"
        )
        proxy_url = f"{GH_PROXY}{raw_url}"

        sources.append({
            "name": fname[:-3],
            "type": "guoyue2010",
            "url_literal": json.dumps(proxy_url, ensure_ascii=False),
        })

    sources.sort(key=lambda x: len(x["name"]))
    return sources


def fetch_pdone_sources():
    """
    扫描 lxSources/pdone/{dir}/latest.js（本地缓存，用于读 @name）
    链接指向上游 pdone/lx-music-source 原地址 + gh-proxy
    """
    if not os.path.isdir(PDONE_DIR):
        print(f"⚠️ 未找到音源目录: {PDONE_DIR}")
        return []

    sources = []

    for dir_name in sorted(os.listdir(PDONE_DIR)):
        dir_path = os.path.join(PDONE_DIR, dir_name)
        if not os.path.isdir(dir_path):
            continue

        latest_path = os.path.join(dir_path, "latest.js")
        if not os.path.isfile(latest_path):
            continue

        try:
            with open(latest_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            print(f"  读取失败 {dir_name}: {e}")
            continue

        display_name = parse_js_name(content) or dir_name

        # 使用上游原仓库链接，而不是本仓库镜像
        encoded_dir = quote(dir_name)
        raw_url = (
            f"https://raw.githubusercontent.com/{PDONE_UPSTREAM}/main/"
            f"{encoded_dir}/latest.js"
        )
        proxy_url = f"{GH_PROXY}{raw_url}"

        sources.append({
            "name": display_name,
            "type": "pdone",
            "url_literal": json.dumps(proxy_url, ensure_ascii=False),
        })

    sources.sort(key=lambda x: len(x["name"]))
    return sources


# ============================================================
# 组装 sections
# ============================================================

def build_sections():
    sections = []

    # 板块 1：软件自动更新列表
    items = fetch_release_items()
    sections.append(section_software_list("🚀 软件自动更新列表", items))

    # 板块 2：洛雪音乐音源（带 guoyue2010 / pdone 分类）
    lx_items = fetch_guoyue2010_sources() + fetch_pdone_sources()
    sections.append(section_copy_cards_grouped("🎵 洛雪音乐音源", lx_items))

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
