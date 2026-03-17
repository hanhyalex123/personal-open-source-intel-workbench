# 分析与日报中文输出 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让文档台分析结果与日报摘要始终以中文输出，历史脏数据和英文回退不再直接暴露给用户。

**Architecture:** 在后端增加统一的中文分析字段判定与兜底逻辑，由 API 和日报构建层负责把系统生成字段收口为中文；前端停止拿英文页面原文充当分析文案。先用运行时清洗解决现网展示，再补最小历史数据修复能力。

**Tech Stack:** Flask, Python, React, Vitest, JSON data store

---

### Task 1: 定义中文分析字段判定规则

**Files:**
- Modify: `backend/app.py`
- Test: `backend/tests/test_api.py`

**Step 1: Write the failing test**

在 `backend/tests/test_api.py` 新增测试，构造英文 `summary_zh` / `doc_summary` / `reading_guide` / `diff_highlights` 的文档事件，断言 `/api/docs/projects/<id>/events` 返回的是中文兜底，而不是英文原文。

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_api.py -q -k chinese_docs`
Expected: FAIL，返回值仍包含英文分析字段。

**Step 3: Write minimal implementation**

在 `backend/app.py` 中新增：
- 中文文本判定函数
- 文档分析字段中文化函数
- 在文档事件聚合时应用该函数

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_api.py -q -k chinese_docs`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app.py backend/tests/test_api.py
git commit -m "fix: normalize docs analysis output to chinese"
```

### Task 2: 让日报构建只输出中文摘要

**Files:**
- Modify: `backend/daily_summary.py`
- Test: `backend/tests/test_daily_summary.py`

**Step 1: Write the failing test**

新增测试，构造只有英文 `title_zh` / `summary_zh` 的证据项，断言 `build_daily_project_summaries` 产出的 `headline`、`summary_zh`、`reason`、`evidence_items` 都是中文模板，不直接暴露英文分析。

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_daily_summary.py -q -k chinese_summary`
Expected: FAIL，日报仍拼出英文标题或摘要。

**Step 3: Write minimal implementation**

在 `backend/daily_summary.py` 中：
- 引入中文字段判定/清洗辅助函数
- 规范 `title_zh`、`summary_zh`
- 调整默认 `headline` 与 `summary_zh` 逻辑，避免直接吃英文证据

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_daily_summary.py -q -k chinese_summary`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/daily_summary.py backend/tests/test_daily_summary.py
git commit -m "fix: keep daily summaries in chinese"
```

### Task 3: 前端停止用英文原文充当分析文案

**Files:**
- Modify: `src/components/DocsWorkbenchPage.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

在 `src/test/app.test.jsx` 新增测试，构造页面 `summary` 为英文、分析字段为空或英文的文档场景，断言：
- 页面列表 teaser 显示中文兜底
- `变化 / 影响 / 建议` 不展示英文分析文案
- 原始 diff 区块保留英文不受影响

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench chinese analysis"`
Expected: FAIL，页面仍显示英文摘要。

**Step 3: Write minimal implementation**

在 `src/components/DocsWorkbenchPage.jsx` 中：
- 增加前端侧中文可用性判断
- 调整 teaser 和右栏回退逻辑
- 仅在原文/ diff 展示区保留英文

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench chinese analysis"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/components/DocsWorkbenchPage.jsx src/test/app.test.jsx
git commit -m "fix: avoid english fallback in docs workbench analysis"
```

### Task 4: 校验首页日报卡不再漏英文

**Files:**
- Modify: `src/components/ProjectSummaryCard.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

新增首页场景测试，构造 evidence 中带英文 `title_zh` / `summary_zh` 的日报卡，断言首页只显示中文摘要或中文模板。

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "cover card chinese summary"`
Expected: FAIL，首页卡片仍显示英文。

**Step 3: Write minimal implementation**

在 `src/components/ProjectSummaryCard.jsx` 中只消费后端中文字段；如后端仍传入不合格文案，则显示中文兜底，不拼英文。

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx -t "cover card chinese summary"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/components/ProjectSummaryCard.jsx src/test/app.test.jsx
git commit -m "fix: keep cover summary cards in chinese"
```

### Task 5: 全量验证

**Files:**
- Modify: none

**Step 1: Run backend focused tests**

Run: `python3 -m pytest backend/tests/test_api.py backend/tests/test_daily_summary.py -q`
Expected: PASS

**Step 2: Run frontend focused tests**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench chinese analysis|cover card chinese summary|empty-response placeholders|docs workbench"`
Expected: PASS

**Step 3: Run build**

Run: `npm run build`
Expected: PASS

**Step 4: Manual verification**

检查：
- `文档台` 的 `页面 / 解读 / 深读` 文案为中文
- 首页 `头条 / 专题 / 快讯` 摘要为中文
- 页面原文和 diff 原文仍可保留英文

**Step 5: Commit**

```bash
git add -A
git commit -m "fix: enforce chinese analysis output"
```
