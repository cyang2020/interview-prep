#!/usr/bin/env python3
"""把 problems/ 下的题目编译成 site/data.js，并跑每一步的测试。

用法：
    python3 build.py            # 编译 + 跑测试
    python3 build.py --no-test  # 只编译
然后用浏览器打开 site/index.html（直接双击即可，不需要起服务）。
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROBLEMS_DIR = ROOT / "problems"
OUT = ROOT / "site" / "data.js"


# ---------------------------------------------------------------- markdown
def _inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s


def _cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def render_md(text):
    lines = text.split("\n")
    out, para = [], []
    i, n = 0, len(lines)

    def flush():
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para.clear()

    while i < n:
        line = lines[i]

        if line.startswith("```"):
            flush()
            lang = line[3:].strip()
            j, buf = i + 1, []
            while j < n and not lines[j].startswith("```"):
                buf.append(lines[j])
                j += 1
            cls = f' class="lang-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(buf))}</code></pre>")
            i = j + 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        if line.startswith(">"):
            flush()
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>" + _inline(" ".join(buf)) + "</p></blockquote>")
            continue

        if line.startswith("|"):
            flush()
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            header = _cells(rows[0])
            body = [_cells(r) for r in rows[1:] if not re.match(r"^\|?\s*:?-{2,}", r.strip())]
            t = "<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in header) + "</tr></thead><tbody>"
            for r in body:
                t += "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>"
            out.append(t + "</tbody></table>")
            continue

        if re.match(r"^\s*[-*]\s+", line):
            flush()
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            flush()
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ol>")
            continue

        if not line.strip():
            flush()
            i += 1
            continue

        para.append(line.strip())
        i += 1

    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- loading
def _read(p):
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _first_h1(md, fallback):
    for line in md.split("\n"):
        m = re.match(r"^#\s+(.*)$", line)
        if m:
            return m.group(1).strip()
    return fallback


def run_tests(step_dir):
    if not (step_dir / "tests.py").exists():
        return None
    try:
        r = subprocess.run(
            [sys.executable, "tests.py"], cwd=step_dir,
            capture_output=True, text=True, timeout=60,
        )
        return {"ok": r.returncode == 0, "output": (r.stdout + r.stderr).strip()[-3000:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "timeout after 60s"}


WARNINGS = []


def load_step(step_dir, do_test):
    notes_md = _read(step_dir / "notes.md")
    title = _first_h1(notes_md, step_dir.name)
    rel = step_dir.relative_to(PROBLEMS_DIR)
    if not notes_md:
        WARNINGS.append(f"{rel}: 缺 notes.md")
    elif not re.match(r"^#\s+第.+问：", notes_md.split(chr(10))[0]):
        WARNINGS.append(f"{rel}/notes.md: 第一行应为 '# 第N问：标题'")
    if "（标题）" in title or "还没写" in _read(step_dir / "tests.py"):
        WARNINGS.append(f"{rel}: 还是骨架模板，内容没填")
    if not (step_dir / "solution.py").exists():
        WARNINGS.append(f"{rel}: 缺 solution.py")
    if not (step_dir / "tests.py").exists():
        WARNINGS.append(f"{rel}: 缺 tests.py")
    label, _, subtitle = title.partition("：")
    files = []
    for name in ("solution.py", "tests.py"):
        if (step_dir / name).exists():
            files.append({"name": name, "content": _read(step_dir / name)})
    for p in sorted(step_dir.iterdir()):
        if p.is_file() and p.name not in ("notes.md", "solution.py", "tests.py") and not p.name.startswith("."):
            files.append({"name": p.name, "content": _read(p)})
    return {
        "id": step_dir.name,
        "title": title,
        "label": label,
        "subtitle": subtitle,
        "notesHtml": render_md(notes_md),
        "files": files,
        "testResult": run_tests(step_dir) if do_test else None,
    }


def load_problem(pdir, do_test):
    meta = json.loads(_read(pdir / "meta.json") or "{}")
    steps_dir = pdir / "steps"
    steps = []
    if steps_dir.exists():
        for sdir in sorted(steps_dir.iterdir()):
            if sdir.is_dir() and not sdir.name.startswith((".", "_")):
                steps.append(load_step(sdir, do_test))
    return {
        "id": pdir.name,
        "meta": meta,
        "problemHtml": render_md(_read(pdir / "problem.md")),
        "overviewHtml": render_md(_read(pdir / "overview.md")),
        "steps": steps,
    }


def main():
    do_test = "--no-test" not in sys.argv
    problems = []
    for pdir in sorted(PROBLEMS_DIR.iterdir()):
        if pdir.is_dir() and (pdir / "meta.json").exists():
            problems.append(load_problem(pdir, do_test))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.PROBLEMS = " + json.dumps(problems, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")

    # 给 index.html 里的 css/js 链接换个版本号，浏览器不会用旧缓存
    import time
    idx = OUT.parent / "index.html"
    idx.write_text(re.sub(r"(style\.css|app\.js|data\.js)\?v=\d+", lambda m: f"{m.group(1)}?v={int(time.time())}", idx.read_text(encoding="utf-8")), encoding="utf-8")

    print(f"wrote {OUT.relative_to(ROOT)}  ({len(problems)} problems)")
    bad = 0
    for p in problems:
        print(f"- {p['id']}: {len(p['steps'])} steps")
        for s in p["steps"]:
            tr = s["testResult"]
            if tr is None:
                status = "no tests" if do_test else "skipped"
            else:
                status = "PASS" if tr["ok"] else "FAIL"
                bad += 0 if tr["ok"] else 1
            print(f"    {s['id']}: {status}" + (f"  {tr['output'].splitlines()[-1]}" if tr and tr["output"] else ""))
    for w in WARNINGS:
        print(f"WARN {w}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
