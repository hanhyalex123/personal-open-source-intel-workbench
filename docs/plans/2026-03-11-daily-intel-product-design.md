# Daily Intel Product Design

**Date:** 2026-03-11

## Goal

将当前“技术情报”页正式改造成一个 `日报产品`，同时保留小时级自动增量更新能力。

用户目标分成两层：

- 白天随时知道哪些项目刚发生了新变化
- 每天固定看到一版稳定、不抖动、可回顾的“每日项目情报”

## Problem

当前系统把“抓取”“单条分析”“首页摘要”混在同一条同步链路里，导致两个问题：

- 首页的时间和内容会因为调度失败或部分刷新而停在昨天
- 首页既像实时流，又像日报，角色不清晰

这和用户的真实使用方式不匹配。用户已经明确表示：

- 旧内容会去 `项目监控` 页自己看
- 首页只要“新的”“最值得看的”
- 每天一版日报，并能进入历史日报回顾

## Product Split

系统拆成两条自动流水线。

### 1. 小时级增量流水线

每 60 分钟自动运行。

职责：

- 抓取每个项目的 GitHub releases 和重点文档入口
- 检测是否有新增或内容变化
- 对变化事件运行单条 LLM 分析
- 直接更新项目监控页数据
- 同步刷新“技术情报”的增量提醒和项目排序

输出：

- `events`
- `analyses`
- `recent_project_updates`

### 2. 每日全盘日报流水线

每天固定时间运行，使用 Asia/Shanghai 时区。

职责：

- 汇总当天或最近一个日报窗口内的项目变化
- 为每个项目生成一张稳定的日报摘要卡
- 固定一版日报，写入历史档案
- 刷新首页主内容

输出：

- `daily_project_summaries`
- `daily_digest_history`

## Data Architecture

数据层应分成四层：

`projects -> events -> analyses -> views`

视图层再拆成：

- `project monitor view`
  - 实时/小时级
- `recent project updates`
  - 小时级增量提醒
- `daily project summaries`
  - 每日固定摘要
- `daily digest history`
  - 历史日报

## Homepage Behavior

首页分成三段。

### Daily Digest

首页第一屏是“今日日报”。

特点：

- 每天固定一版
- 不因为小时级同步频繁抖动
- 默认只展示每个项目最值得看的摘要卡

### Incremental Updates

日报下方单独展示“自日报之后的新变化”。

特点：

- 小时级自动更新
- 只放新增提醒，不重写整版日报
- 点进去跳项目监控页

### History

首页底部展示“历史日报”入口。

特点：

- 只列日期和摘要数量
- 不和实时增量混在一起

## Scheduler and Heartbeat

状态层需要记录真实时间，而不是只写一个 `running: true`。

最少需要这些状态字段：

- `last_fetch_success_at`
- `last_incremental_analysis_at`
- `last_daily_digest_at`
- `last_heartbeat_at`
- `scheduler.incremental`
- `scheduler.daily_digest`

页面显示逻辑：

- 最近抓取成功
- 最近增量分析
- 最近日报生成
- 调度是否正常

如果超过阈值未刷新，应明确展示“当前展示的是旧日报”。

## LLM Responsibilities

大模型必须自动参与内容分析，但不能接管调度和页面结构。

### LLM should do

- 单条 release/doc 事件分析
- 项目级日报摘要
- 增量提醒摘要
- 风险、动作、标签判断

### LLM should not do

- 不负责决定任务何时运行
- 不直接控制页面排版
- 不做“手动运营”

页面结构必须由前端模板渲染，LLM 只产出结构化字段。

## Ordering Rules

### Project Monitor

- 小时级更新
- 以真实新变化优先

### Incremental Updates

- 过去 24 小时内新发生的变化
- 高风险优先

### Daily Digest

- 过去一个日报窗口内的项目摘要
- 以项目重要度、风险、动作项排序
- 当天固定，不跟小时级刷新乱跳

## Failure Handling

- 抓取失败不应覆盖旧日报
- 单项目分析失败不影响其他项目
- 日报生成失败时首页继续展示上一版日报，并标记“未完成今日刷新”
- 增量提醒可独立失败，不影响项目监控页

## UI Direction

首页是日报产品，不再是纯 dashboard。

因此视觉上应强调：

- 今日日报
- 增量提醒
- 历史日报

而不是继续堆统计卡和来源列表。
