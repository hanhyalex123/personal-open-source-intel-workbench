# 开源情报站品牌与 README 现状化 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把项目对外品牌更新为“架构师开源情报站”，并为 README 增加现状截图与架构图。

**Architecture:** 保持现有前后端结构不变，只更新对外可见文案与说明文档。图片资产放在 `docs/assets/`，README 通过相对路径引用。组件文件名保持现状，避免引入无意义重构。

**Tech Stack:** React + Vite, Flask, Markdown, SVG, PNG, Vitest, Pytest

---

### Task 1: 更新品牌文案测试与实现

**Files:**
- Modify: `backend/tests/test_start_script.py`
- Modify: `src/test/app.test.jsx`
- Modify: `src/App.jsx`
- Modify: `backend/prompts.py`
- Modify: `scripts/start_intel_workbench.sh`
- Modify: `scripts/stop_intel_workbench.sh`

**Step 1: Write the failing test**

- 在 `src/test/app.test.jsx` 断言新品牌文案 `架构师` 与 `开源情报站` 出现
- 在 `backend/tests/test_start_script.py` 断言启动脚本输出新品牌名

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx && .venv/bin/python -m pytest -q backend/tests/test_start_script.py`
Expected: FAIL on old brand strings

**Step 3: Write minimal implementation**

- 更新 `src/App.jsx` 品牌区文案
- 更新 `backend/prompts.py` 中的产品名
- 更新启动/停止脚本中的输出文案

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx && .venv/bin/python -m pytest -q backend/tests/test_start_script.py`
Expected: PASS

**Step 5: Commit**

```bash
git add src/App.jsx src/test/app.test.jsx backend/prompts.py scripts/start_intel_workbench.sh scripts/stop_intel_workbench.sh backend/tests/test_start_script.py
git commit -m "feat: rename product brand"
```

### Task 2: 增加 README 架构图与截图资产

**Files:**
- Create: `docs/assets/architecture-overview.svg`
- Create: `docs/assets/screenshot-home.png`
- Create: `docs/assets/screenshot-sync-monitor.png`
- Create: `docs/assets/screenshot-project-monitor.png`

**Step 1: Generate assets**

- 绘制一张静态 SVG 架构图，覆盖浏览器、Flask API、调度器、本地 JSON、外部来源与模型网关
- 运行本地服务并截取首页、同步监控、情报监控页面截图

**Step 2: Verify assets exist**

Run: `ls docs/assets`
Expected: 列出 `architecture-overview.svg` 和三张截图

**Step 3: Commit**

```bash
git add docs/assets
git commit -m "docs: add architecture and ui screenshots"
```

### Task 3: 重写 README 为现状版展示

**Files:**
- Modify: `README.md`

**Step 1: Write the failing doc check**

- 用 `rg` 检查 README 中旧标题是否仍存在

**Step 2: Run check to verify it fails**

Run: `rg -n "中文运维情报面板|Intel Workbench" README.md`
Expected: FIND matches

**Step 3: Write minimal implementation**

- 标题改为 `架构师开源情报站`
- 增加产品简介、架构图、界面截图、能力说明、启动方式和数据目录
- 保留现状导向，不写未实现功能

**Step 4: Run check to verify it passes**

Run: `rg -n "中文运维情报面板|Intel Workbench" README.md`
Expected: no matches

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: refresh readme for current product state"
```

### Task 4: 全量验证

**Files:**
- Modify: none

**Step 1: Run frontend tests**

Run: `npm test`
Expected: PASS

**Step 2: Run backend targeted tests**

Run: `.venv/bin/python -m pytest -q backend/tests/test_start_script.py`
Expected: PASS

**Step 3: Run production build**

Run: `npm run build`
Expected: PASS

**Step 4: Commit**

```bash
git status --short
```

Expected: no unintended changes
