# Ant Design 控制台与排序体系 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 引入 Ant Design 5 统一前端控制台组件体系，并将日报排序与监控排序拆成两套独立评分逻辑，优先重做封面、线索台、研究台。

**Architecture:** 前端通过 `ConfigProvider + Layout + Card/Table/List` 建立统一控制台壳层和页面骨架，逐步替换现有散装 JSX/CSS；后端把“日报排序”和“监控排序”从同一组分数拆成两个明确函数，并在 `/api/dashboard` 中分别返回消费结果与解释信息。

**Tech Stack:** React 18, Vite, Ant Design 5, Flask, pytest, vitest

---

### Task 1: 引入 Ant Design 与主题基线

**Files:**
- Modify: `package.json`
- Create: `src/theme/antdTheme.js`
- Modify: `src/main.jsx`

**Step 1: 写失败测试**
- 断言应用入口被 `ConfigProvider` 包裹
- 断言主主题 token 生效的最小渲染结果

**Step 2: 运行测试确认失败**
- Run: `npm test -- src/test/app.test.jsx`

**Step 3: 最小实现**
- 安装 `antd`
- 新增统一 theme token
- 在入口挂载 `ConfigProvider`

**Step 4: 运行测试确认通过**
- Run: `npm test -- src/test/app.test.jsx`

**Step 5: 提交**
- Run: `git add package.json src/main.jsx src/theme/antdTheme.js src/test/app.test.jsx`
- Run: `git commit -m "feat: add antd theme foundation"`

### Task 2: 重做应用壳层为控制台布局

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/index.css`
- Test: `src/test/app.test.jsx`

**Step 1: 写失败测试**
- 断言侧边导航使用统一菜单
- 断言顶部页头与内容容器存在

**Step 2: 运行测试确认失败**
- Run: `npm test -- src/test/app.test.jsx`

**Step 3: 最小实现**
- 使用 `Layout`, `Sider`, `Header`, `Content`
- 保留现有页面路由状态，不改业务数据流
- 统一导航、页头、主内容容器

**Step 4: 运行测试确认通过**
- Run: `npm test -- src/test/app.test.jsx`

**Step 5: 提交**
- Run: `git add src/App.jsx src/index.css src/test/app.test.jsx`
- Run: `git commit -m "feat: add antd workbench shell"`

### Task 3: 拆日报排序与监控排序的后端测试

**Files:**
- Modify: `backend/tests/test_daily_summary.py`
- Modify: `backend/tests/test_api.py`

**Step 1: 写日报排序测试**
- 同一批项目中，近期有更新的项目应优先进入日报卡片
- 超出 `must_watch_days` / `emerging_days` 的项目不出现在日报卡片

**Step 2: 写监控排序测试**
- 同一批项目中，30 天变化量高且最近仍更新的项目在项目榜更靠前
- 监控排序结果允许与日报排序不同

**Step 3: 运行测试确认失败**
- Run: `python3 -m pytest backend/tests/test_daily_summary.py backend/tests/test_api.py -q`

**Step 4: 提交测试**
- Run: `git add backend/tests/test_daily_summary.py backend/tests/test_api.py`
- Run: `git commit -m "test: define digest and monitor ranking behavior"`

### Task 4: 实现日报排序与监控排序拆分

**Files:**
- Modify: `backend/daily_ranking.py`
- Modify: `backend/daily_summary.py`
- Modify: `backend/app.py`

**Step 1: 实现日报排序函数**
- 保留窗口过滤
- 把新鲜度、重要度、30 天活跃度、已读衰减合成日报分数

**Step 2: 实现监控排序函数**
- 使用 30 天变化量、最近更新时间、项目基础权重、已读衰减

**Step 3: 在 dashboard payload 中区分返回**
- `homepage_projects`
- `project_board`
- 必要的排序解释字段

**Step 4: 运行测试确认通过**
- Run: `python3 -m pytest backend/tests/test_daily_summary.py backend/tests/test_api.py -q`

**Step 5: 提交**
- Run: `git add backend/daily_ranking.py backend/daily_summary.py backend/app.py`
- Run: `git commit -m "feat: split digest and monitor ranking"`

### Task 5: 重做封面页为 Ant Design 控制台结构

**Files:**
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/components/ProjectSummaryCard.jsx`
- Modify: `src/components/ProjectRankBoard.jsx`
- Modify: `src/components/DailyDigestHistory.jsx`
- Modify: `src/components/ArchiveDigestPanel.jsx`
- Modify: `src/index.css`
- Test: `src/test/app.test.jsx`

**Step 1: 写失败测试**
- 断言封面主要区块存在：头条、快讯、项目榜、专题、归档
- 断言关键区块改为统一 `Card` 语义渲染

**Step 2: 运行测试确认失败**
- Run: `npm test -- src/test/app.test.jsx`

**Step 3: 最小实现**
- 用 `Card`, `Row`, `Col`, `List`, `Statistic`, `Badge`, `Tag`
- 统一封面信息层级
- 减少页面级自定义视觉噪音

**Step 4: 运行测试确认通过**
- Run: `npm test -- src/test/app.test.jsx`

**Step 5: 提交**
- Run: `git add src/components/IntelOverviewPage.jsx src/components/ProjectSummaryCard.jsx src/components/ProjectRankBoard.jsx src/components/DailyDigestHistory.jsx src/components/ArchiveDigestPanel.jsx src/index.css src/test/app.test.jsx`
- Run: `git commit -m "feat: rebuild cover page with antd"`

### Task 6: 重做线索台为运行控制台

**Files:**
- Modify: `src/components/SyncMonitorPage.jsx`
- Modify: `src/components/SyncStatusPanel.jsx`
- Modify: `src/components/SyncJobList.jsx`
- Modify: `src/components/SyncLogDrawer.jsx`
- Modify: `src/index.css`
- Test: `src/test/app.test.jsx`

**Step 1: 写失败测试**
- 断言当前任务、历史任务、日志入口有统一层级
- 断言运行状态与失败信息更易读

**Step 2: 运行测试确认失败**
- Run: `npm test -- src/test/app.test.jsx`

**Step 3: 最小实现**
- 用 `Card`, `Table`, `Drawer`, `Tag`, `Progress`, `Descriptions`
- 强化当前任务与历史任务区分

**Step 4: 运行测试确认通过**
- Run: `npm test -- src/test/app.test.jsx`

**Step 5: 提交**
- Run: `git add src/components/SyncMonitorPage.jsx src/components/SyncStatusPanel.jsx src/components/SyncJobList.jsx src/components/SyncLogDrawer.jsx src/index.css src/test/app.test.jsx`
- Run: `git commit -m "feat: rebuild sync console with antd"`

### Task 7: 重做研究台为查询/证据/结果工作区

**Files:**
- Modify: `src/components/AIConsolePage.jsx`
- Modify: `src/index.css`
- Test: `src/test/app.test.jsx`

**Step 1: 写失败测试**
- 断言查询区、证据区、结果区布局清晰
- 断言模型信息、证据数量、搜索链路状态可见

**Step 2: 运行测试确认失败**
- Run: `npm test -- src/test/app.test.jsx`

**Step 3: 最小实现**
- 用 `Card`, `Form`, `Select`, `Input`, `Typography`, `List`, `Alert`, `Tag`
- 把报告结果与模型状态做成明确的可视区块

**Step 4: 运行测试确认通过**
- Run: `npm test -- src/test/app.test.jsx`

**Step 5: 提交**
- Run: `git add src/components/AIConsolePage.jsx src/index.css src/test/app.test.jsx`
- Run: `git commit -m "feat: rebuild research console with antd"`

### Task 8: 补排序解释与最终验证

**Files:**
- Modify: `src/components/ProjectRankBoard.jsx`
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `backend/daily_summary.py`
- Test: `backend/tests/test_daily_summary.py`
- Test: `src/test/app.test.jsx`

**Step 1: 写失败测试**
- 断言日报/监控排序说明可见
- 断言项目榜 tooltip 展示排序因子

**Step 2: 运行测试确认失败**
- Run: `python3 -m pytest backend/tests/test_daily_summary.py -q`
- Run: `npm test -- src/test/app.test.jsx`

**Step 3: 最小实现**
- 后端补排序解释字段
- 前端统一 `?` / tooltip 入口

**Step 4: 运行完整验证**
- Run: `python3 -m pytest backend/tests/test_daily_summary.py backend/tests/test_api.py backend/tests/test_runtime.py -q`
- Run: `npm test -- src/test/app.test.jsx`
- Run: `npm run build`

**Step 5: 提交**
- Run: `git add backend src docs/plans`
- Run: `git commit -m "feat: unify console ui with antd and refine ranking"`
