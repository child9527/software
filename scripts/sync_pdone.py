#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 pdone/lx-music-source 根目录下各子目录的 latest.js
到本仓库 lxSources/pdone/{dirname}/latest.js
"""

import os
import sys
import re
import shutil
import requests
from datetime import datetime, timezone, timedelta

PDONE_REPO = "pdone/lx-music-source"
OUTPUT_ROOT = os.path.join("lxSources", "pdone")
TIMEOUT = 30
TZ = timezone(timedelta(hours=8))


def log(msg: str):
    print(f"[{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def list_top_dirs(headers: dict) -> list:
    url = f"https://api.github.com/repos/{PDONE_REPO}/contents/"
    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    dirs = []
    for entry in resp.json():
        if entry.get("type") != "dir":
            continue
        name = entry["name"]
        if name.startswith("."):
            continue
        dirs.append(name)
    return sorted(dirs)


def download_latest(dir_name: str, headers: dict) -> tuple:
    """返回 (ok, content_or_error)"""
    url = f"https://raw.githubusercontent.com/{PDONE_REPO}/main/{dir_name}/latest.js"
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 404:
            return False, "no latest.js"
        if resp.status_code != 200:
            return False, f"http {resp.status_code}"
        return True, resp.content
    except requests.RequestException as e:
        return False, str(e)


def parse_name(content: bytes) -> str:
    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    m = re.search(r"@name\s+(.+)", text)
    return m.group(1).strip() if m else ""


def main():
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or ""
    headers = {"User-Agent": "child9527-software-sync"}
    if token:
        headers["Authorization"] = f"token {token}"

    log(f"开始同步 {PDONE_REPO} → {OUTPUT_ROOT}")

    try:
        dirs = list_top_dirs(headers)
    except Exception as e:
        log(f"获取目录列表失败: {e}")
        sys.exit(1)

    log(f"发现一级目录: {', '.join(dirs)}")

    # 重建输出目录，保证与上游一致
    if os.path.exists(OUTPUT_ROOT):
        shutil.rmtree(OUTPUT_ROOT)
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    ok_count = 0
    for d in dirs:
        ok, data = download_latest(d, headers)
        if not ok:
            log(f"  跳过 {d}: {data}")
            continue

        out_dir = os.path.join(OUTPUT_ROOT, d)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "latest.js")
        with open(out_path, "wb") as f:
            f.write(data)

        name = parse_name(data) or d
        log(f"  ✅ {d}/latest.js → {name} ({len(data)} bytes)")
        ok_count += 1

    if ok_count == 0:
        log("未同步到任何文件")
        sys.exit(1)

    log(f"完成，共同步 {ok_count} 个音源")


if __name__ == "__main__":
    main()
