# Intel Workbench Phase 2 Design

**Date:** 2026-03-09

## Goal

在现有多页面工作台基础上，解决首页卡片布局失衡问题，明确区分 `技术情报` 与 `项目监控`，并把 `AI 控制台` 接到本地 assistant API，同时用全局配置文件统一控制 assistant 行为。

## Scope

本轮只做三类变化：

- 重排前端页面结构和样式，修复当前多列项目卡造成的拥挤与层叠观感。
- 新增本地 assistant 查询接口和全局 assistant 配置接口。
- 将配置中心扩展为“全局 assistant 配置 + 项目配置/crawl profile”双层后台。

## Information Architecture

### 技术情报

技术情报页只展示跨项目摘要，不再承载项目级卡片墙。

主要内容：

- 工作台总览
- 高影响变化列表
- 技术分类聚合
- 来源覆盖范围

页面形态以摘要卡、列表和横向分区为主，强调范围、趋势和分类。

### 项目监控

项目监控页专门做按项目下钻。

主要内容：

- 项目头部信息
- `ReleaseNote 区`
- `文档区`

采用单列项目流，每个项目内部再分块展示，避免首页双列大卡压缩导致的视觉问题。

### AI 控制台

AI 控制台定位为本地知识助手，不做代码执行。

界面分为左右两列：

- 左侧：问题输入框、项目筛选、分类筛选、时间范围筛选、提交按钮
- 右侧：回答、关键依据、来源、建议下一步

### 配置中心

配置中心拆成两个区域：

- 全局 assistant 配置
- 项目列表与 crawl profile

## Assistant Data Flow

前端调用本地 `POST /api/assistant/query`，请求包含：

- `query`
- `project_ids`
- `categories`
- `timeframe`

后端执行顺序：

1. 读取全局 assistant 配置
2. 合并前端显式筛选条件
3. 对 query 做轻量分类
4. 从本地 `events + analyses` 组织候选结果
5. 返回统一结构化回答

返回结构：

- `answer`
- `evidence`
- `next_steps`
- `sources`
- `applied_filters`

## Assistant Configuration

assistant 配置保存在现有 `backend/data/config.json` 的 `assistant` 字段内。

配置项包括：

- `enabled`
- `default_project_ids`
- `default_categories`
- `default_timeframe`
- `max_evidence_items`
- `max_source_items`
- `retrieval.release_weight`
- `retrieval.docs_weight`
- `prompts.classification`
- `prompts.answer`

配置中心负责读取和更新这份全局配置。

## Testing Strategy

后端先补红灯测试：

- `POST /api/assistant/query`
- `GET/PUT /api/config`

前端再补红灯测试：

- `技术情报` 与 `项目监控` 的信息和文案明显不同
- `AI 控制台` 展示输入区、筛选器、答案区、来源区
- 配置中心展示 assistant 全局配置表单

最后统一验证：

- `python3 -m pytest backend/tests -q`
- `npm test`
- `npm run build`
