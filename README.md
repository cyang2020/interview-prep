# interviewPrep

线上地址：https://cyang2020.github.io/interview-prep/ 。改完题后运行 `./deploy.sh "提交说明"`：它会跑 build.py、推 main、再把 site/ 推成 gh-pages 分支发布。

面试题库站：每道题有题面、整体思路、若干小问；每一小问能看思路、这一问的完整代码，以及和上一问（或任意一问）的 diff。

## 怎么看

```
python3 build.py        # 把 problems/ 编译成 site/data.js，并跑每一步的测试
open site/index.html    # 直接双击打开即可，不需要起服务
```

## 目录结构

```
problems/<题目id>/
  meta.json          标题、公司、标签、阶段
  problem.md         题面（原题要点 + 大白话讲解）
  overview.md        整体思路（状态表、数据结构、面试节奏、追问）
  steps/<序号-名字>/
    notes.md         这一问的思路。第一行 "# 第N问：标题" 会变成页签
    solution.py      做到这一步的完整代码
    tests.py         这一步的测试，from solution import ...，直接 python3 tests.py 能跑
site/
  index.html / app.js / style.css   前端，纯静态，无依赖
  data.js                           build.py 生成，不要手改
```

## 加一道新题

```
python3 new_problem.py <题目id> --steps basic,ttl,capacity   # 生成骨架
# 按 AGENTS.md 填内容
python3 build.py                                            # 必须全 PASS
```

让别的 agent 来加题：把 `PROMPT.md` 里那段话加上题面发给它，它会自己读 `AGENTS.md`。

diff 是在浏览器里按行算的（最长公共子序列），所以每一问的 `solution.py` 都写成完整文件，不要只写增量。
