(function () {
  "use strict";
  const PROBLEMS = window.PROBLEMS || [];
  const app = document.getElementById("app");

  // ---------------------------------------------------------------- state
  const state = {
    view: null,              // 代码栏在看什么：diff | full | tests；null = 按默认（第一问看完整代码，其余看对比）
    base: null,              // 对比基准：step index，null = 上一问
    collapse: true,          // 对比时只看改动附近
    ws: true,                // 对比时忽略空白
    wrap: null,              // 代码长行是否折行；null = 窄屏折行、宽屏不折
    testsDiff: false,        // 测试用例视图：只看相对基准新增的
    pane: "notes",           // 窄屏（放不下两栏）时看哪一栏：notes | code
    expanded: new Set(),     // 已展开的折叠段 "from-to"
  };
  const esc = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const twoCols = () => window.innerWidth >= 720;
  const wrapOn = () => state.wrap === null ? window.innerWidth < 1200 : state.wrap;

  function route() {
    const h = location.hash.replace(/^#/, "");
    const [pid, view] = h.split("/");
    const problem = PROBLEMS.find(p => p.id === pid) || PROBLEMS[0];
    if (!problem) return { problem: null };
    let v = view || "problem";
    if (v.startsWith("s")) {
      const idx = parseInt(v.slice(1), 10);
      if (!(idx >= 1 && idx <= problem.steps.length)) v = "problem";
    }
    return { problem, view: v };
  }

  // ---------------------------------------------------------------- diff
  function diffLines(a, b, norm) {
    const n = a.length, m = b.length;
    const ka = a.map(norm), kb = b.map(norm);
    const dp = new Array(n + 1);
    for (let i = 0; i <= n; i++) dp[i] = new Uint16Array(m + 1);
    for (let i = n - 1; i >= 0; i--)
      for (let j = m - 1; j >= 0; j--)
        dp[i][j] = ka[i] === kb[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    const ops = [];
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (ka[i] === kb[j]) { ops.push({ t: "ctx", o: i + 1, n: j + 1, s: b[j] }); i++; j++; }
      else if (dp[i + 1][j] >= dp[i][j + 1]) { ops.push({ t: "del", o: i + 1, s: a[i] }); i++; }
      else { ops.push({ t: "add", n: j + 1, s: b[j] }); j++; }
    }
    while (i < n) { ops.push({ t: "del", o: i + 1, s: a[i] }); i++; }
    while (j < m) { ops.push({ t: "add", n: j + 1, s: b[j] }); j++; }
    return ops;
  }

  // ---------------------------------------------------------------- highlight (python)
  const KW = new Set("False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield self".split(" "));
  const TOK = /(#.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|([A-Za-z_][A-Za-z0-9_]*)|(\d+(?:\.\d+)?)|(\s+|.)/g;
  function hl(line) {
    let out = "", m;
    TOK.lastIndex = 0;
    while ((m = TOK.exec(line))) {
      if (m[1]) out += `<span class="c">${esc(m[1])}</span>`;
      else if (m[2]) out += `<span class="s">${esc(m[2])}</span>`;
      else if (m[3]) out += KW.has(m[3]) ? `<span class="k">${m[3]}</span>` : m[3];
      else if (m[4]) out += `<span class="n">${m[4]}</span>`;
      else out += esc(m[5]);
      if (m[0] === "") TOK.lastIndex++;
    }
    return out || "&nbsp;";
  }

  // ---------------------------------------------------------------- render helpers
  function fileOf(step, name) {
    const f = step && step.files.find(f => f.name === name);
    return f ? f.content : "";
  }
  const tableOpen = () => `<table class="code${wrapOn() ? " wrap" : ""}">`;

  function renderFull(text) {
    const lines = text.replace(/\n$/, "").split("\n");
    let h = tableOpen();
    lines.forEach((s, i) => { h += `<tr><td class="ln">${i + 1}</td><td class="mk"></td><td>${hl(s)}</td></tr>`; });
    return h + "</table>";
  }

  function renderDiff(oldText, newText) {
    const a = oldText.replace(/\n$/, "").split("\n");
    const b = newText.replace(/\n$/, "").split("\n");
    if (oldText === "") a.length = 0;
    const norm = state.ws ? (x => x.replace(/\s+/g, " ").trim()) : (x => x);
    const ops = diffLines(a, b, norm);
    const adds = ops.filter(o => o.t === "add").length, dels = ops.filter(o => o.t === "del").length;
    if (!adds && !dels) return { html: '<div class="empty">和对比基准完全相同</div>', adds, dels };

    const CONTEXT = 3;
    const show = ops.map(() => !state.collapse);
    if (state.collapse) {
      ops.forEach((o, k) => {
        if (o.t === "ctx") return;
        for (let d = -CONTEXT; d <= CONTEXT; d++) if (ops[k + d]) show[k + d] = true;
      });
    }
    let h = tableOpen(), k = 0;
    const row = o => {
      const cls = o.t === "add" ? "add" : o.t === "del" ? "del" : "";
      const mk = o.t === "add" ? "+" : o.t === "del" ? "−" : "";
      const ln = o.t === "del" ? o.o : o.n;
      return `<tr class="${cls}"><td class="ln">${ln}</td><td class="mk">${mk}</td><td>${hl(o.s)}</td></tr>`;
    };
    while (k < ops.length) {
      if (show[k]) { h += row(ops[k]); k++; continue; }
      const from = k;
      while (k < ops.length && !show[k]) k++;
      const key = `${from}-${k}`;
      if (state.expanded.has(key)) { for (let x = from; x < k; x++) h += row(ops[x]); }
      else h += `<tr class="fold" data-fold="${key}"><td colspan="3">⋯ ${k - from} 行没变，点击展开 ⋯</td></tr>`;
    }
    return { html: h + "</table>", adds, dels };
  }

  // 思路正文：核心思路 / 思考与反问 / 测试要点 直接展示，其余小节默认折叠
  const OPEN_SECTIONS = new Set(["这一问要做什么", "核心思路", "思考与反问", "测试要点"]);
  function notesBody(html) {
    const parts = html.split(/(?=<h2>)/);
    const hasNew = parts.some(p => { const m = p.match(/^<h2>(.*?)<\/h2>/); return m && OPEN_SECTIONS.has(m[1].trim()); });
    if (!hasNew) return html;
    let out = "", folded = "";
    for (const p of parts) {
      const m = p.match(/^<h2>(.*?)<\/h2>/);
      if (!m || OPEN_SECTIONS.has(m[1].trim())) out += p;
      else folded += p.replace(/^<h2>(.*?)<\/h2>/, "");
    }
    if (folded.trim()) out += `<details class="more"><summary>更多说明</summary><div class="morebody">${folded}</div></details>`;
    return out;
  }

  function sidebar(problem) {
    const items = PROBLEMS.map(p => {
      const m = p.meta || {};
      return `<li><a href="#${p.id}/problem" class="${problem && p.id === problem.id ? "active" : ""}">
        <div class="t">${esc(m.title_zh || m.title || p.id)}</div>
        <div class="s">${esc(m.title && m.title_zh ? m.title : "")}</div>
      </a></li>`;
    }).join("");
    return `<aside class="sidebar"><h1>Interview Prep</h1><ul class="plist">${items}</ul></aside>`;
  }

  function header(problem, view) {
    const m = problem.meta || {};
    const tab = (id, label, sub) => `<a href="#${problem.id}/${id}" class="${view === id ? "active" : ""}">${label}${sub ? `<span class="sub">${esc(sub)}</span>` : ""}</a>`;
    const tabs = [tab("problem", "题面"), tab("overview", "整体思路")]
      .concat(problem.steps.map((s, i) => tab(`s${i + 1}`, esc(s.label), s.subtitle))).join("");
    const psel = `<select class="psel" data-set="problem">${PROBLEMS.map(p => `<option value="${p.id}" ${p.id === problem.id ? "selected" : ""}>${esc((p.meta || {}).title_zh || (p.meta || {}).title || p.id)}</option>`).join("")}</select>`;
    return `<header class="phead">
      <div class="titlebar">${psel}<h2 class="ptitle">${esc(m.title_zh || m.title || problem.id)}<span class="en">${esc(m.title_zh ? m.title : "")}</span></h2></div>
      <nav class="tabs">${tabs}</nav></header>`;
  }

  function stepView(problem, idx) {
    const step = problem.steps[idx];
    const baseIdx = state.base === null ? idx - 1 : state.base;
    const base = baseIdx >= 0 && baseIdx < problem.steps.length && baseIdx !== idx ? problem.steps[baseIdx] : null;
    const view = state.view || (idx === 0 ? "full" : "diff");   // 第一问没有上一问，默认看完整代码
    const tr = step.testResult;

    const sol = fileOf(step, "solution.py"), tests = fileOf(step, "tests.py");
    let body, stats = "", banner = "";
    if (view === "diff") {
      const r = renderDiff(base ? fileOf(base, "solution.py") : "", sol);
      body = r.html;
      stats = `<span class="stats"><span class="a">+${r.adds}</span><span class="d">−${r.dels}</span></span>`;
    } else if (view === "full") {
      body = sol ? renderFull(sol) : '<div class="empty">这一步没有 solution.py</div>';
    } else {
      if (tr) banner = `<div class="testbanner ${tr.ok ? "ok" : "bad"}">${tr.ok ? "✓ " : "✗ "}${esc(tr.ok ? (tr.output || "").trim().split("\n").pop() || "测试通过" : "测试失败")}</div>` + (tr.ok ? "" : `<pre class="testout">${esc(tr.output || "")}</pre>`);
      if (!tests) body = '<div class="empty">这一步没有 tests.py</div>';
      else if (state.testsDiff) {
        const r = renderDiff(base ? fileOf(base, "tests.py") : "", tests);
        body = r.html;
        stats = `<span class="stats"><span class="a">+${r.adds}</span><span class="d">−${r.dels}</span></span>`;
      } else body = renderFull(tests);
    }

    const baseOpts = problem.steps.map((s, i) => i === idx ? "" :
      `<option value="${i}" ${i === baseIdx ? "selected" : ""}>${esc(s.label)}${i === idx - 1 ? "（上一问）" : ""}</option>`).join("")
      + `<option value="-1" ${baseIdx < 0 ? "selected" : ""}>空文件</option>`;
    const diffOpts = `<label>基准 <select data-set="base">${baseOpts}</select></label>
          <label><input type="checkbox" data-set="collapse" ${state.collapse ? "checked" : ""}> 折叠未变</label>
          <label><input type="checkbox" data-set="ws" ${state.ws ? "checked" : ""}> 忽略空白</label>`;
    const dot = tr ? `<i class="dot ${tr.ok ? "ok" : "bad"}"></i>` : "";

    const prev = idx > 0 ? `<a href="#${problem.id}/s${idx}">← ${esc(problem.steps[idx - 1].label)}</a>` : `<a href="#${problem.id}/overview">← 整体思路</a>`;
    const next = idx + 1 < problem.steps.length ? `<a href="#${problem.id}/s${idx + 2}">${esc(problem.steps[idx + 1].label)} →</a>` : `<span class="dis">已是最后一问</span>`;

    const pane = twoCols() ? "both" : state.pane;
    const paneBar = twoCols() ? "" : `<div class="panebar"><span class="seg">
        <button data-pane="notes" class="${pane === "notes" ? "on" : ""}">思路</button>
        <button data-pane="code" class="${pane === "code" ? "on" : ""}">代码${dot}</button></span></div>`;

    return `${paneBar}<div class="step pane-${pane}">
      <article class="notes md">${notesBody(step.notesHtml)}<nav class="stepnav innotes">${prev}${next}</nav></article>
      <section class="codecol">
        <div class="toolbar">
          <span class="seg">
            <button data-view="diff" class="${view === "diff" ? "on" : ""}">对比</button>
            <button data-view="full" class="${view === "full" ? "on" : ""}">完整代码</button>
            <button data-view="tests" class="${view === "tests" ? "on" : ""}">测试用例${dot}</button>
          </span>
          ${view === "diff" ? diffOpts : ""}
          ${view === "tests" ? `<label><input type="checkbox" data-set="testsDiff" ${state.testsDiff ? "checked" : ""}> 只看本问新增</label>${state.testsDiff ? diffOpts : ""}` : ""}
          ${stats}
          <label class="right"><input type="checkbox" data-set="wrap" ${wrapOn() ? "checked" : ""}> 折行</label>
        </div>
        ${banner}
        <div class="codeview">${body}</div>
        <nav class="stepnav">${prev}${next}</nav>
      </section>
    </div>`;
  }

  function render() {
    const { problem, view } = route();
    if (!problem) { app.innerHTML = `<aside class="sidebar"><h1>Interview Prep</h1></aside><main class="main"><div class="empty">problems/ 下还没有题目，先运行 python3 build.py</div></main>`; return; }
    let content;
    if (view === "problem") content = `<div class="content scroll"><article class="doc md">${problem.problemHtml}</article></div>`;
    else if (view === "overview") content = `<div class="content scroll"><article class="doc md">${problem.overviewHtml}</article></div>`;
    else content = `<div class="content">${stepView(problem, parseInt(view.slice(1), 10) - 1)}</div>`;
    app.innerHTML = sidebar(problem) + `<main class="main">${header(problem, view)}${content}</main>`;
    document.title = `${(problem.meta || {}).title_zh || problem.id} · Interview Prep`;
    const act = app.querySelector(".tabs a.active");
    if (act && act.scrollIntoView) act.scrollIntoView({ block: "nearest", inline: "center" });
  }

  // ---------------------------------------------------------------- events
  app.addEventListener("click", e => {
    const v = e.target.closest("button[data-view]");
    if (v) { state.view = v.dataset.view; state.expanded.clear(); render(); return; }
    const p = e.target.closest("button[data-pane]");
    if (p) { state.pane = p.dataset.pane; render(); return; }
    const f = e.target.closest("tr.fold");
    if (f) { state.expanded.add(f.dataset.fold); render(); }
  });
  app.addEventListener("change", e => {
    const el = e.target.closest("[data-set]");
    if (!el) return;
    const k = el.dataset.set;
    if (k === "problem") { location.hash = `#${el.value}/problem`; return; }
    if (k === "base") { state.base = parseInt(el.value, 10); state.expanded.clear(); }
    else if (k === "collapse") { state.collapse = el.checked; state.expanded.clear(); }
    else if (k === "ws") { state.ws = el.checked; state.expanded.clear(); }
    else if (k === "wrap") state.wrap = el.checked;
    else if (k === "testsDiff") { state.testsDiff = el.checked; state.expanded.clear(); }
    render();
  });
  window.addEventListener("hashchange", () => { state.base = null; state.expanded.clear(); render(); });
  let lastCols = twoCols();
  window.addEventListener("resize", () => { if (twoCols() !== lastCols) { lastCols = twoCols(); render(); } });
  render();
})();
