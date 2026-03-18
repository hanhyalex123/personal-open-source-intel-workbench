# 封面信息流澄清 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重排封面信息流，明确 `快讯 / 项目榜 / 头条 / 归档` 的职责，补齐历史日报点击和 README 更新。

**Architecture:** 后端把封面数据拆成“主卡片区”和“监控榜”两套口径：主卡片继续遵守 x/y 天窗口，项目榜改成监控老项目 + 当前新项目，并输出 30 天趋势与解释字段；前端重排封面结构、补齐点击行为、删除无价值入口，并新增归档详情面板。README 采用简洁开源首页结构，并重截截图。

**Tech Stack:** Flask, React, Vite, pytest, vitest, Playwright headless screenshot script

---

### Task 1: 锁定后端封面数据新口径

**Files:**
- Modify: `backend/tests/test_api.py`
- Modify: `backend/tests/test_daily_summary.py`

**Step 1: 写 `project_board` 保留 stale must-watch 的失败测试**
- 构造一个超过 `must_watch_days` 的老项目和一个近期新项目。
- 断言：
  - 老项目不在 `headline/topic` 主卡片候选里
  - 但仍在 `project_board` 里

**Step 2: 写 `project_board` 输出 30 天趋势与 breakdown 测试**
- 断言字段包含：
  - `activity_series_30d`
  - `activity_breakdown_30d`
  - `board_explanation`

**Step 3: 写 `/api/daily-digests/<date>` 失败测试**
- 断言存在按日期读取日报摘要的接口。
- 断言返回该日期的 `summaries`。

**Step 4: 运行测试确认失败**
- Run: `python3 -m pytest backend/tests/test_api.py backend/tests/test_daily_summary.py -q`
- Expected: FAIL

**Step 5: Commit**
```bash
git add backend/tests/test_api.py backend/tests/test_daily_summary.py
git commit -m "test: define clarified cover dashboard payload"
```

### Task 2: 实现后端封面数据与历史日报接口

**Files:**
- Modify: `backend/app.py`
- Modify: `backend/daily_summary.py`
- Modify: `backend/daily_ranking.py`
- Modify: `backend/digest_history.py`

**Step 1: 调整 `project_board` 监控范围**
- `must_watch` 项目：始终进入榜单
- `emerging` 项目：沿用当前窗口自动进入

**Step 2: 把趋势从 7 天改为 30 天**
- 输出 `activity_series_30d`
- 输出 `activity_breakdown_30d = { total, release, docs }`

**Step 3: 生成榜单解释字段**
- 返回简短可展示的 `board_explanation`
- 返回 tooltip 需要的结构化解释字段

**Step 4: 新增历史日报接口**
- 例如：`GET /api/daily-digests/<date>`
- 直接从 `daily_project_summaries` 读，不重新生成

**Step 5: 运行测试确认通过**
- Run: `python3 -m pytest backend/tests/test_api.py backend/tests/test_daily_summary.py -q`
- Expected: PASS

**Step 6: Commit**
```bash
git add backend/app.py backend/daily_summary.py backend/daily_ranking.py backend/digest_history.py backend/tests/test_api.py backend/tests/test_daily_summary.py
git commit -m "feat: clarify cover dashboard payload and archive api"
```

### Task 3: 锁定前端封面行为

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: 写封面顺序测试**
- 断言顺序为：
  - `头条`
  - `快讯`
  - `项目榜`
  - `专题`
  - `归档`
- 断言 `入口` 不再出现

**Step 2: 写 `项目榜` tooltip 与 30 天文案测试**
- 断言能看到 `30天`
- 断言 tooltip 中出现 `release` / `docs` 解释

**Step 3: 写 `快讯` 点击行为测试**
- docs 项点击后进入 `文档台` 或调用对应回调
- release 项点击后跳转来源 URL 或调用 open handler

**Step 4: 写 `归档` 点击测试**
- 点击某个日期后，请求历史日报接口
- 断言出现 `归档详情`

**Step 5: 运行测试确认失败**
- Run: `npm test -- src/test/app.test.jsx -t '封面|项目榜|快讯|归档'`
- Expected: FAIL

**Step 6: Commit**
```bash
git add src/test/app.test.jsx
git commit -m "test: define clarified cover interactions"
```

### Task 4: 实现前端封面交互

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/lib/api.js`
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/components/IncrementalUpdateList.jsx`
- Modify: `src/components/ProjectRankBoard.jsx`
- Modify: `src/components/DailyDigestHistory.jsx`
- Create: `src/components/ArchiveDigestPanel.jsx`
- Modify: `src/index.css`

**Step 1: 删除 `入口` 区块并重排封面**
- 顺序改成：`头条 -> 快讯 -> 项目榜 -> 专题 -> 归档`

**Step 2: 改造 `快讯`**
- 副说明收成一句：`日报后新增`
- 增加 docs / release 点击行为

**Step 3: 改造 `项目榜`**
- 使用 `activity_series_30d`
- 加 `?` tooltip，解释统计口径与排序

**Step 4: 改造 `归档`**
- 日期卡改成按钮
- 点击加载 `归档详情`
- 详情内渲染当天的项目摘要卡

**Step 5: 运行前端测试确认通过**
- Run: `npm test -- src/test/app.test.jsx -t '封面|项目榜|快讯|归档'`
- Expected: PASS

**Step 6: Commit**
```bash
git add src/App.jsx src/lib/api.js src/components/IntelOverviewPage.jsx src/components/IncrementalUpdateList.jsx src/components/ProjectRankBoard.jsx src/components/DailyDigestHistory.jsx src/components/ArchiveDigestPanel.jsx src/index.css src/test/app.test.jsx
git commit -m "feat: clarify cover information flow"
```

### Task 5: README 与截图更新

**Files:**
- Modify: `README.md`
- Modify: `docs/assets/screenshot-home.png`
- Modify: `docs/assets/screenshot-sync-monitor.png`
- Modify/Create: `docs/assets/screenshot-docs-workbench.png` or `docs/assets/screenshot-settings.png`
- Optional Create: `scripts/capture_readme_screenshots.mjs`

**Step 1: 收紧 README 结构**
- 保留一句话介绍、核心能力、架构、启动、截图
- 删除过长说明段

**Step 2: 重新截图**
- 启动前后端
- 截取最新封面
- 截取线索台
- 截取文档台或设置页

**Step 3: 替换 README 图片引用**
- 确保路径正确

**Step 4: 运行构建验证**
- Run: `npm run build`
- Expected: PASS

**Step 5: Commit**
```bash
git add README.md docs/assets
git commit -m "docs: refresh readme and screenshots"
```

### Task 6: 整体验证并推送

**Files:**
- Modify: 上述涉及文件

**Step 1: 运行后端测试**
- Run: `python3 -m pytest backend/tests/test_api.py backend/tests/test_daily_summary.py -q`
- Expected: PASS

**Step 2: 运行前端测试**
- Run: `npm test -- src/test/app.test.jsx -t '封面|项目榜|快讯|归档'`
- Expected: PASS

**Step 3: 运行构建**
- Run: `npm run build`
- Expected: PASS

**Step 4: 手工验证**
- Run: `python3 -m backend.server`
- Run: `npm run dev -- --host 0.0.0.0 --port 5173`
- 检查：
  - `入口` 已删除
  - `快讯` 在 `项目榜` 之前
  - `项目榜` 为 30 天图
  - stale must-watch 项目不再占 `头条 / 专题`
  - `归档` 可点击并能展开详情

**Step 5: Push**
```bash
git push origin main
```
