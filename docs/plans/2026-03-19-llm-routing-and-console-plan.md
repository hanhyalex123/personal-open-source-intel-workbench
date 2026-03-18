# LLM 路由与控制台改版 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为同步、日报、研究建立统一的 LLM failover 路由器，加入 preflight 硬门禁，并把模型链路展示到前端与日志中，同时将设置页重做为更规整的控制台风格。

**Architecture:** 后端新增统一 LLM route 解析与 preflight 探活层，所有分析/研究入口复用该层；同步 job 在启动前先进行 LLM preflight，失败则直接阻断；前端设置页改为基于 route 列表的控制台式配置和状态展示。

**Tech Stack:** Flask, React, Vite, pytest, vitest

---

### Task 1: 写失败测试，锁定 LLM failover 行为

**Files:**
- Modify: `backend/tests/test_llm_requests.py`

**Step 1: 写 5.4 失败后切到 5.2 的测试**
- 模拟第一条 route 返回 503
- 模拟第二条 route 返回正常 JSON
- 断言最终结果来自第二条 route
- 断言 `_llm.used_fallback == true`
- 断言 `_llm.model == gpt-5.2`

**Step 2: 写双 route 都失败时的测试**
- 两次请求都返回 503
- 断言抛出 `LLMRequestError`
- 断言错误包含主模型和备用模型信息

**Step 3: 运行测试确认失败**
- Run: `python3 -m pytest backend/tests/test_llm_requests.py -q`

### Task 2: 实现 route 列表解析与 failover

**Files:**
- Modify: `backend/llm.py`
- Modify: `backend/storage.py`

**Step 1: 给配置增加 `openai.routes` 兼容读取**
**Step 2: 保留旧单路由字段向后兼容**
**Step 3: 实现按 priority 的 route 选择**
**Step 4: 实现 ordered failover：5.4 -> 5.2**
**Step 5: 把 `route_alias` 和 fallback 元信息写入 `_llm`**

**Step 6: 运行测试**
- Run: `python3 -m pytest backend/tests/test_llm_requests.py -q`

### Task 3: 写 preflight 阻断测试

**Files:**
- Modify: `backend/tests/test_sync.py`
- Modify: `backend/tests/test_assistant.py`

**Step 1: 写同步 preflight 失败时不启动 crawl 的测试**
- 断言 repo/feed fetcher 未被调用
- 断言结果状态为 failed / blocked

**Step 2: 写研究报告 preflight 失败的测试**
- 断言返回明确失败信息，而不是空响应占位文案

**Step 3: 运行测试确认失败**
- Run: `python3 -m pytest backend/tests/test_sync.py backend/tests/test_assistant.py -q`

### Task 4: 实现 preflight 硬门禁

**Files:**
- Modify: `backend/llm.py`
- Modify: `backend/sync.py`
- Modify: `backend/sync_status.py`
- Modify: `backend/assistant.py`

**Step 1: 增加最小 preflight 请求函数**
**Step 2: 同步 job 开始前执行 preflight**
**Step 3: preflight 失败则 source 标记为 blocked，不继续 crawl**
**Step 4: 研究请求入口执行 preflight**
**Step 5: 失败返回明确错误文案**

**Step 6: 运行测试**
- Run: `python3 -m pytest backend/tests/test_sync.py backend/tests/test_assistant.py -q`

### Task 5: 扩展日志与日报模型展示

**Files:**
- Modify: `backend/sync.py`
- Modify: `backend/daily_summary.py`
- Modify: `backend/app.py`
- Modify: `backend/assistant.py`
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/components/AIConsolePage.jsx`

**Step 1: 在 sync log 中加入 provider/model/route_alias/fallback 字段**
**Step 2: 日报项目对象增加模型元信息**
**Step 3: 研究报告响应增加模型元信息**
**Step 4: 前端显示“本次模型 / 降级情况”**

**Step 5: 运行后端与前端相关测试**
- Run: `python3 -m pytest backend/tests/test_api.py -q`
- Run: `npm test -- src/test/app.test.jsx`

### Task 6: 重做模型设置页为阿里云风格

**Files:**
- Modify: `src/components/SettingsPage.jsx`
- Modify: `src/index.css`
- Modify: `src/test/app.test.jsx`

**Step 1: 将模型页改成概览 + 路由表 + 策略卡布局**
**Step 2: 将单路由编辑改成 route 列表编辑**
**Step 3: 用开关替换零散 checkbox 视觉**
**Step 4: 显示最近探活结果与主备关系**

**Step 5: 运行前端测试与构建**
- Run: `npm test -- src/test/app.test.jsx`
- Run: `npm run build`

### Task 7: 重做助手设置页为分组卡片

**Files:**
- Modify: `src/components/SettingsPage.jsx`
- Modify: `src/index.css`
- Modify: `src/test/app.test.jsx`

**Step 1: 拆成默认范围 / 检索策略 / Prompt 三个卡块**
**Step 2: 压缩表单密度，统一标签与输入间距**
**Step 3: 用更贴近控制台的卡片和分隔线样式**

**Step 4: 运行前端测试与构建**
- Run: `npm test -- src/test/app.test.jsx`
- Run: `npm run build`

### Task 8: 端到端验证与提交

**Files:**
- Modify: 以上涉及文件

**Step 1: 运行关键后端测试**
- Run: `python3 -m pytest backend/tests/test_llm_requests.py backend/tests/test_sync.py backend/tests/test_assistant.py backend/tests/test_api.py -q`

**Step 2: 运行关键前端测试**
- Run: `npm test -- src/test/app.test.jsx`

**Step 3: 启动前后端并手工验证**
- Run: `python3 -m backend.server`
- Run: `npm run dev -- --host 0.0.0.0 --port 5173`

**Step 4: 提交**
- Run: `git add backend src docs/plans`
- Run: `git commit -m "Implement llm failover and console redesign"`
