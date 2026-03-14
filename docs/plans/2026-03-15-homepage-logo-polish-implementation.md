# 首页品牌头图与 Logo 强化 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 强化 `架构师开源情报站` 的侧边栏品牌区和首页封面，让项目更适合公开展示，同时不改动现有功能结构。

**Architecture:** 只调整 `src/App.jsx`、`src/components/IntelOverviewPage.jsx` 和 `src/index.css` 的展示层。数据流、接口和页面导航保持不变。通过纯 CSS 徽记和轻量文案实现品牌升级，避免引入新依赖。

**Tech Stack:** React, Vite, CSS, Vitest

---

### Task 1: 为品牌区写失败测试并实现新结构

**Files:**
- Modify: `src/test/app.test.jsx`
- Modify: `src/App.jsx`

**Step 1: Write the failing test**
- 断言品牌定位文案出现
- 断言导航项带有图标辅助文案或 aria 标签

**Step 2: Run test to verify it fails**
Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL on new brand elements missing

**Step 3: Write minimal implementation**
- 在 `src/App.jsx` 中加入品牌徽记、定位文案、导航图标

**Step 4: Run test to verify it passes**
Run: `npm test -- src/test/app.test.jsx`
Expected: PASS

### Task 2: 强化首页封面与视觉壳层

**Files:**
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/index.css`

**Step 1: Implement display changes**
- 首页封面增加刊头信息、产品短宣言和更强的层级
- 样式补齐品牌徽记、导航图标、封面信息条和更强的配色层次

**Step 2: Run tests**
Run: `npm test -- src/test/app.test.jsx`
Expected: PASS

### Task 3: 更新 README 截图

**Files:**
- Modify: `docs/assets/screenshot-home.png`
- Modify: `README.md` if wording needs alignment

**Step 1: Start local app and capture fresh screenshot**
- 重新截取首页，确保 README 展示的是新品牌版本

**Step 2: Verify asset exists**
Run: `ls -lh docs/assets/screenshot-home.png`
Expected: file present with updated timestamp

### Task 4: Full verification and prepare for push

**Files:**
- Modify: none

**Step 1: Run full frontend tests**
Run: `npm test`
Expected: PASS

**Step 2: Run production build**
Run: `npm run build`
Expected: PASS

**Step 3: Inspect git status**
Run: `git status --short`
Expected: only intended tracked changes plus pre-existing untracked files
