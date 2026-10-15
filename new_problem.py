#!/usr/bin/env python3
"""生成一道新题的骨架。

用法：
    python3 new_problem.py lru-cache --steps 3
    python3 new_problem.py lru-cache --steps basic,ttl,capacity --title "LRU Cache" --company OpenAI
生成后按 AGENTS.md 填内容，再 python3 build.py。
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CN = "一二三四五六七八九十"


def cn(n):
    return CN[n - 1] if 1 <= n <= 10 else str(n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("problem_id", help="英文小写加短横线，例如 lru-cache")
    ap.add_argument("--steps", default="2", help="小问数量，或逗号分隔的英文名，例如 basic,ttl")
    ap.add_argument("--title", default="", help="英文原题名")
    ap.add_argument("--title-zh", default="", help="中文题名")
    ap.add_argument("--company", default="")
    a = ap.parse_args()

    pdir = ROOT / "problems" / a.problem_id
    if pdir.exists():
        raise SystemExit(f"{pdir} 已存在，不覆盖")

    names = [s.strip() for s in a.steps.split(",")] if not a.steps.isdigit() else [f"step{i}" for i in range(1, int(a.steps) + 1)]

    pdir.mkdir(parents=True)
    (pdir / "meta.json").write_text(json.dumps({
        "title": a.title or a.problem_id,
        "title_zh": a.title_zh or a.title or a.problem_id,
        "company": a.company,
        "stage": "",
        "frequency": "",
        "last_asked": "",
        "tags": [],
        "language": "python",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (pdir / "problem.md").write_text(
        "# 题面\n\n"
        "## 题目\n\n- （一句话：要写什么东西）\n- （方法名(参数)：干什么）\n- 第一问：\n\n"
        "## 要问清楚的地方\n\n- \n", encoding="utf-8")

    (pdir / "overview.md").write_text(
        "# 整体思路\n\n**一句话。** \n\n**各问是叠加关系。** \n\n"
        "## 全部状态转移\n\n| 当前状态 | 触发 | 条件 | 下一状态 |\n|---|---|---|---|\n\n"
        "## 数据结构\n\n| 结构 | 存什么 | 回答什么问题 | 第几问出现 |\n|---|---|---|---|\n\n"
        "## 面试节奏\n\n- \n\n"
        "## 常见追问\n\n| 追问 | 答法 |\n|---|---|\n", encoding="utf-8")

    for i, name in enumerate(names, 1):
        sdir = pdir / "steps" / f"{i:02d}-{name}"
        sdir.mkdir(parents=True)
        (sdir / "notes.md").write_text(
            f"# 第{cn(i)}问：（标题）\n\n## 这一问要做什么\n\n- \n\n## 核心思路\n\n- \n\n"
            "## 思考与反问\n\n- \n\n"
            "## 测试要点\n\n- test_xxx：\n\n"
            "## 更多说明\n\n### \n\n", encoding="utf-8")
        (sdir / "solution.py").write_text("# 做到这一步的完整代码\n", encoding="utf-8")
        (sdir / "tests.py").write_text(
            "from solution import *\n\n\n"
            f"def test_todo():\n    assert False, \"第{cn(i)}问的测试还没写\"\n\n\n"
            "if __name__ == \"__main__\":\n    tests = [test_todo]\n    for t in tests:\n        t()\n"
            "    print(f\"all {len(tests)} passed\")\n", encoding="utf-8")

    print(f"created {pdir.relative_to(ROOT)} with steps: {', '.join(f'{i:02d}-{n}' for i, n in enumerate(names, 1))}")
    print("next: 按 AGENTS.md 填内容，然后 python3 build.py")


if __name__ == "__main__":
    main()
