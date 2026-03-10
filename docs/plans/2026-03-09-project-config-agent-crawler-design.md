# Project Config Agent Crawler Design

**Date:** 2026-03-09

## Goal

把当前“固定几个源 + 手工灌结果”的监控面板升级成一个可配置的项目监控系统。每个项目由 `GitHub URL + 官方文档 URL` 组成，系统自动建立项目、抓取 release notes、发现文档结构、按技术类别聚合文档结论，并在前台按项目分区展示 `ReleaseNote 区` 与 `文档区`。

## Product Shape

每个项目都是一个独立监控单元，具备：

- `ReleaseNote 区`
  - 基于 GitHub releases / changelog
  - 产出版本变化、兼容性风险、升级动作
- `文档区`
  - 基于官方文档站点
  - 不是首页摘要，而是抓取章节后按技术域聚合
  - 技术域包括：网络、存储、调度、架构、安全、升级、运行时、可观测性

如果某项目没有有效文档源，可以只保留 `ReleaseNote 区`。

## Project Configuration Model

新增项目时，用户只需要提供：

- `name`
- `github_url`
- `docs_url`

系统自动生成：

- GitHub repo 标识
- release 抓取配置
- docs crawl profile 草稿
- 文档分类规则草稿
- 调度配置

项目配置记录的核心字段：

- `id`
- `name`
- `github_url`
- `docs_url`
- `enabled`
- `sync_interval_minutes`
- `release_area_enabled`
- `docs_area_enabled`
- `created_at`
- `updated_at`

## Agent-Assisted Docs Discovery

文档站点结构不稳定，不能假设每个站点都有固定字段或统一目录。新项目接入时，必须有一层 `发现 Agent` 参与。

发现 Agent 的职责：

- 判断文档站点类型（Docusaurus / Hugo / 自定义站点等）
- 找导航入口、目录树、版本入口、语言入口、sitemap
- 识别哪些页面是正文页，哪些是导航页、归档页、搜索页
- 生成 `crawl profile`

`crawl profile` 是可编辑的后台配置，至少包含：

- `entry_urls`
- `allowed_path_prefixes`
- `blocked_path_prefixes`
- `version_roots`
- `language_roots`
- `max_depth`
- `expand_mode`
- `category_hints`
- `discovery_prompt`
- `classification_prompt`

## Docs Crawling and Record Shape

文档抓取层采用“弱结构”记录，不要求每页都有完整字段。

单个文档页记录尽量包含：

- `project_id`
- `url`
- `title`
- `path`
- `section`
- `body`
- `content_hash`
- `last_seen_at`
- `source_type`
- `category`
- `extractor_hint`

其中：

- `url`、`body`、`content_hash`、`last_seen_at` 是强依赖
- `title`、`path`、`section` 允许为空
- `category` 可以先由规则得出，再由轻量 LLM 修正

## Docs Classification

文档页会被分类到统一的运维技术域：

- 网络
- 存储
- 调度
- 架构
- 安全
- 升级
- 运行时
- 可观测性

分类优先级：

1. URL path / breadcrumb / nav title
2. 正文关键词与术语
3. 轻量 LLM 兜底分类

文档区最终展示的是“按技术域聚合的最新结论”，而不是逐页原文堆叠。

## Daily Audit

系统每天定时执行一次“结构巡检”，目标不是只抓增量，还要确认没有漏抓。

巡检内容：

- 文档导航 / sitemap 是否变化
- 已知章节是否消失
- 是否出现新目录、新版本、新语言入口
- 页面正文是否异常变短或抽空
- 现有 crawl profile 是否需要更新

若发现结构漂移：

- 记录 drift 告警
- 自动触发一次 `发现 Agent` 重跑
- 生成新的 `crawl profile draft`
- 在后台展示差异，允许人工确认

## Stability Requirements

量大时稳定性优先于“全量精读”。系统需要满足：

- 单条模型调用失败不拖垮整轮同步
- 文档正文进入模型前必须裁剪
- 先做规则分类，再做少量高价值 LLM 补充
- 所有发现结果和 crawl profile 持久化
- 支持项目级别的启停与频率配置

## Admin Backend

后台分成三块：

### 1. Project Config

- 新增 / 编辑项目
- 填写 GitHub URL 与官方文档 URL
- 控制是否启用 release 区和文档区

### 2. Crawl Profile

- 查看与编辑发现 Agent 生成的 crawl profile
- 查看 prompts
- 调整路径白名单 / 黑名单 / 技术域提示

### 3. Audit & Review

- 结构漂移告警
- 新发现文档分类
- 高影响 release / docs 结论
- 失败抓取与失败分析记录

## Frontend Layout

前台分三层：

### 1. Top Overview

- 最近同步时间
- 新增高影响结论数
- 结构漂移项目数
- 需要关注的项目数

### 2. Project Sections

每个项目一块，项目内分：

- `ReleaseNote 区`
- `文档区`

### 3. Insight Cards

卡片统一结构：

- 标题
- 一句话结论
- 关键变化点
- 影响范围
- 建议动作
- 标签
- 来源链接
- 固定结论标记

文档区内再按技术分类折叠展示。

## Out of Scope for This Iteration

- 任意网址自动推断项目 repo 与文档源
- 多用户权限系统
- 分布式任务队列
- 浏览器推送通知
- 全站浏览器渲染抓取

## Risks

- 文档站点结构千差万别，发现 Agent 的 profile 质量决定后续稳定性
- 若对所有文档页都跑重型 LLM，成本和时延会失控
- GitHub release 与文档结论需要合并展示，但不能互相污染

## Recommendation

先做“一个项目 = GitHub URL + 官方文档 URL”的显式双源模型，不做全自动推断。先把项目配置后台、crawl profile、日常巡检和 source-first UI 建稳，再逐步增强 Agent 自动发现能力。
