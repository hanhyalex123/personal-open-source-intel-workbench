# High-Impact Unified Stream Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有按仓库分散展示的监控页升级为跨仓库统一“高影响更新流”，突出影响分析、为什么重要、建议动作、优先级与标签，并预留可替换的 LLM 分析接口。

**Architecture:** 保留前端直连 GitHub/feed 的轻量抓取方式，把 commits/releases/issues/feed 统一映射为标准事件，再通过“规则分析器 + Provider 抽象”的双层结构生成洞察卡片。页面首页改为事件流 + 关注域概览，后续可由 OpenClaw 或独立分析站复用同一分析层。

**Tech Stack:** React 18、Vite 5、Tailwind CSS 3、Vitest、Testing Library。

---

### Task 1: 建立可测试的统一事件与分析层

**Files:**
- Create: `src/lib/dashboard-model.js`
- Create: `src/lib/dashboard-model.test.js`

**Step 1: Write the failing test**
- 为 GitHub commit/release/issue/feed 到统一事件的转换写测试。
- 为高影响分类、优先级、标签、建议动作、关键词域识别写测试。
- 为 LLM provider fallback 行为写测试。

**Step 2: Run test to verify it fails**
- Run: `npm test -- --runInBand`
- Expected: FAIL，提示模块或导出不存在。

**Step 3: Write minimal implementation**
- 实现标准事件结构。
- 实现基于规则的影响分析与排序。
- 实现 `createAnalyzer` 抽象，支持 `rule-based`、`mock-llm` 与外部 provider 注入。

**Step 4: Run test to verify it passes**
- Run: `npm test -- --runInBand`
- Expected: PASS。

### Task 2: 重构首页为统一高影响更新流

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/index.css`

**Step 1: Write the failing test**
- 在组件测试中断言首页存在统一更新流、优先级/标签/建议动作展示、LLM 模式提示。

**Step 2: Run test to verify it fails**
- Run: `npm test -- --runInBand`
- Expected: FAIL。

**Step 3: Write minimal implementation**
- 将原有 repo/feed 拉取结果接入统一事件层。
- 新增首页摘要、筛选与高影响卡片。
- 保留原始仓库/文档视图作为辅助面板。

**Step 4: Run test to verify it passes**
- Run: `npm test -- --runInBand`
- Expected: PASS。

### Task 3: 补充文档与最终验证

**Files:**
- Modify: `README.md`
- Modify: `package.json`

**Step 1: Update docs**
- 说明新的首页结构、测试命令、LLM/OpenClaw 接口设计。

**Step 2: Run verification**
- Run: `npm test -- --runInBand`
- Run: `npm run build`
- Expected: 全部通过。
