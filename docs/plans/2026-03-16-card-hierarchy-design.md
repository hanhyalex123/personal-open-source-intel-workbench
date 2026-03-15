# Card Hierarchy Visual Refresh Design

## Goal
强化全站卡片层级感，让重要内容更突出、次要信息更克制，整体保持现有柔和玻璃质感，不改变功能与布局结构。

## Scope
- LLM 配置区全部卡片（Provider 卡、Effective Config、表单块）。
- 同步日志详情（Detail 面板、行、原始日志折叠块）。
- 其他页面卡片统一继承层级 tokens，不改布局。

## Non-Goals
- 不新增功能、不改动数据逻辑。
- 不调整布局结构（保持现有 DOM/网格）。

## Visual Hierarchy System
定义三档卡片层级：
- **Hero**: 核心信息区块，最突出，白底、实线边框、更强阴影。
- **Focus**: 次级重点区块，浅色底、更明显边框、柔和阴影。
- **Base**: 常规卡片，保留当前风格，稍微加强边框与对比。

通过 CSS tokens 实现（示例）：
- `--card-hero-bg`, `--card-hero-border`, `--card-hero-shadow`
- `--card-focus-bg`, `--card-focus-border`, `--card-focus-shadow`
- `--card-base-bg`, `--card-base-border`, `--card-base-shadow`

## Component Mapping
- **Hero**: Effective Config 区块（突出“生效配置”信息）
- **Focus**: 同步日志详情面板、Provider 卡片
- **Base**: 其余卡片与表单块

## Interaction & Readability
- 行与块增加清晰分隔（row divider）
- tag/label 更明确（chip/label 胶囊 + 微弱高对比背景）
- 原始日志 `pre` 更像“内嵌面板”

## Risks
- 阴影过强会破坏现有玻璃质感
- 层级太多会显得“花”，需要克制

## Testing
- 视觉回归：确认关键卡片层级清晰
- 不需要新增单元测试
