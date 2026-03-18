# 项目榜 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为封面页新增一个只基于日报候选项目的 `项目榜`，用最近更新时间、7 天趋势、权重分和已读次数帮助用户快速决定先看谁。

**Architecture:** 后端在现有日报 bucket 基础上新增 `project_board` 聚合结果，计算候选项目的最近活动、7 天趋势、已读次数和榜单分；前端在封面页新增单独榜单组件，使用轻量 SVG sparkline 展示 7 天趋势，并支持点击滚动到对应日报卡片。

**Tech Stack:** Flask, React, Vite, pytest, vitest

---

### Task 1: 锁定后端榜单输出

**Files:**
- Modify: `backend/tests/test_api.py`
- Modify: `backend/tests/test_daily_summary.py`

**Step 1: 写 dashboard 返回 `project_board` 的失败测试**
- 在 `backend/tests/test_api.py` 增加一个用例。
- 断言 `/api/dashboard` 返回 `project_board`。
- 断言榜单只包含 `must_watch_projects + emerging_projects` 中的项目。

**Step 2: 写窗口过滤测试**
- 在 `backend/tests/test_daily_summary.py` 增加一个用例。
- 构造一个高重要度但超出窗口的项目。
- 断言它不会进入榜单。

**Step 3: 写排序测试**
- 构造两个候选项目：
  - 一个更重要但 5 天前更新
  - 一个 6 小时前更新
- 断言最近更新的项目优先。

**Step 4: 写已读衰减测试**
- 构造两个同分候选项目。
- 给其中一个增加最近已读记录。
- 断言已读项目在榜单中排后。

**Step 5: 运行测试确认失败**
- Run: `python3 -m pytest backend/tests/test_api.py backend/tests/test_daily_summary.py -q`
- Expected: FAIL，提示 `project_board` 缺失或排序不符合预期

**Step 6: Commit**
```bash
git add backend/tests/test_api.py backend/tests/test_daily_summary.py
git commit -m "test: define project rank board payload"
```

### Task 2: 实现后端项目榜聚合

**Files:**
- Modify: `backend/daily_summary.py`
- Modify: `backend/daily_ranking.py`
- Modify: `backend/app.py`

**Step 1: 在 `backend/daily_summary.py` 新增候选项目榜构建函数**
- 例如：`build_project_rank_board(snapshot, summary_date, now_iso)`。
- 输入直接复用现有日报 bucket。

**Step 2: 计算榜单信号**
- 每个候选项目补齐：
  - `last_activity_at`
  - `updates_7d`
  - `activity_series_7d`
  - `read_count`
  - `read_decay_applied`

**Step 3: 在 `backend/daily_ranking.py` 增加榜单分计算**
- 新增一个明确的 `compute_project_board_score(...)`。
- 默认权重：
  - 新鲜度 `0.40`
  - 重要度 `0.30`
  - 7 天更新强度 `0.20`
  - 已读衰减 `0.10`

**Step 4: 在 `backend/app.py` 的 `/api/dashboard` 中返回 `project_board`**
- 不替换现有 `homepage_projects`
- 仅新增字段，保持兼容

**Step 5: 运行测试确认通过**
- Run: `python3 -m pytest backend/tests/test_api.py backend/tests/test_daily_summary.py -q`
- Expected: PASS

**Step 6: Commit**
```bash
git add backend/daily_summary.py backend/daily_ranking.py backend/app.py backend/tests/test_api.py backend/tests/test_daily_summary.py
git commit -m "feat: add daily candidate project board payload"
```

### Task 3: 写前端榜单渲染失败测试

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: 扩展 dashboard mock**
- 给 `dashboardPayload` 增加 `project_board`。
- 每项包含：
  - `project_id`
  - `project_name`
  - `last_activity_label`
  - `board_score`
  - `read_count`
  - `activity_series_7d`

**Step 2: 写封面页渲染测试**
- 断言有 `项目榜` 标题。
- 断言能看到：
  - 最近更新时间标签
  - 权重分
  - 已读次数

**Step 3: 写点击滚动测试**
- 模拟点击榜单条目。
- 断言调用 `scrollIntoView` 或定位到对应 `data-project-id` 卡片。

**Step 4: 写空态测试**
- `project_board = []`
- 断言显示空态文案。

**Step 5: 运行测试确认失败**
- Run: `npm test -- src/test/app.test.jsx -t '项目榜'`
- Expected: FAIL，提示榜单组件或文案缺失

**Step 6: Commit**
```bash
git add src/test/app.test.jsx
git commit -m "test: define project board cover behavior"
```

### Task 4: 实现前端项目榜组件

**Files:**
- Create: `src/components/ProjectRankBoard.jsx`
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/components/ProjectSummaryCard.jsx`
- Modify: `src/index.css`

**Step 1: 新建 `ProjectRankBoard.jsx`**
- 渲染榜单列表。
- 使用内联 SVG 渲染 `activity_series_7d` sparkline。

**Step 2: 在 `IntelOverviewPage.jsx` 接入 `project_board`**
- 在 `头条` 下方、`专题` 上方插入 `项目榜` 区块。
- 不影响现有 `头条 / 专题 / 快讯 / 归档` 布局。

**Step 3: 给 `ProjectSummaryCard.jsx` 保持可滚动定位**
- 保留或补齐 `data-project-id`。
- 确保榜单点击可以滚到对应卡片。

**Step 4: 在 `src/index.css` 添加榜单样式**
- 行级布局
- 短标签样式
- sparkline 容器
- hover/focus 状态

**Step 5: 运行测试确认通过**
- Run: `npm test -- src/test/app.test.jsx -t '项目榜'`
- Expected: PASS

**Step 6: Commit**
```bash
git add src/components/ProjectRankBoard.jsx src/components/IntelOverviewPage.jsx src/components/ProjectSummaryCard.jsx src/index.css src/test/app.test.jsx
git commit -m "feat: add cover project rank board"
```

### Task 5: 做整体验证

**Files:**
- Modify: 以上涉及文件

**Step 1: 运行关键后端测试**
- Run: `python3 -m pytest backend/tests/test_api.py backend/tests/test_daily_summary.py -q`
- Expected: PASS

**Step 2: 运行关键前端测试**
- Run: `npm test -- src/test/app.test.jsx -t '项目榜|封面'`
- Expected: PASS

**Step 3: 运行构建**
- Run: `npm run build`
- Expected: PASS

**Step 4: 手工验证**
- Run: `python3 -m backend.server`
- Run: `npm run dev -- --host 0.0.0.0 --port 5173`
- 检查：
  - 封面页出现 `项目榜`
  - 只展示日报候选项目
  - 最近 3 天无更新的近期项目不再上榜
  - 点击榜单可定位到日报卡片

**Step 5: Commit**
```bash
git add backend src
git commit -m "feat: surface daily candidate project board"
```
