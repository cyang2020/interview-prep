#!/bin/sh
# 发布到 GitHub Pages：先跑 build.py（跑测试 + 生成 site/data.js），
# 再把 main 推上去，最后把 site/ 目录单独推成 gh-pages 分支。
set -e
cd "$(dirname "$0")"
python3 build.py
git add -A
git diff --cached --quiet || git commit -m "${1:-更新题库}"
git push origin main
site_commit=$(git subtree split --prefix site main 2>/dev/null | tr -d '\r' | grep -o '[0-9a-f]\{40\}' | tail -1)
git push origin "${site_commit}:refs/heads/gh-pages" --force
echo "已发布：https://cyang2020.github.io/interview-prep/"
