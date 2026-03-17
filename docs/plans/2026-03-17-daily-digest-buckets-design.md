# 日报分区（老牌必看 + 近期更新）设计

## 目标
- 日报只展示“最近更新”的项目，避免旧项目常驻
- 由你手动配置两类项目清单：老牌必看 / 小项目・新项目・AI 项目
- 老牌必看看 30 天，小项目看 3 天
- 修正“来源 14/16”统计口径，避免误解

## 背景问题
- 现有日报会回退旧项目，导致缺乏时效性
- 手动日报显示“来源 14/16”但无失败/跳过，统计口径不一致

## 方案概览
- 配置两份项目清单 + 两个时间窗口
- 日报生成时按窗口过滤，仅输出有近期更新的项目
- 同时保留扁平 `homepage_projects` 兼容现有 UI

## 配置
新增 `daily_digest` 配置块：
```
{
  "daily_digest": {
    "must_watch_project_ids": [],
    "emerging_project_ids": [],
    "must_watch_days": 30,
    "emerging_days": 3
  }
}
```

- `must_watch_project_ids`: 老牌必看（项目级）
- `emerging_project_ids`: 小项目 / 新项目 / AI 项目（项目级）
- 均为你在设置页手动选择
- 仅在窗口内有更新时才显示

## 日报生成逻辑
1. 计算项目最新更新日期：
   - 取该项目所有已分析事件的 `published_at` 或 `last_seen_at`
   - 作为“最近更新”时间
2. 过滤与分区：
   - 老牌必看区：在 `must_watch_project_ids` 且最近更新 ≤ 30 天
   - 近期更新区：在 `emerging_project_ids` 且最近更新 ≤ 3 天
3. 区内排序：
   - 继续使用已实现的 `ranking_score`（权重 + 已读衰减 + MMR）
4. 输出结构：
   - `must_watch_projects`
   - `emerging_projects`
   - `homepage_projects = must_watch + emerging`（兼容旧 UI）

## UI 设计
- 设置页新增“日报分区”配置：
  - 老牌必看项目（多选）
  - 小项目/新项目/AI 项目（多选）
  - 时间窗口（可编辑，默认 30 / 3）

## 来源统计修正
- 日报阶段 `total_sources` 使用 **实际文档源数量（feeds）**
- 可选在 UI 显示：`文档源 X/X | 项目 N`

## 测试
- 后端：
  - 老牌必看只在 30 天内出现
  - 小项目只在 3 天内出现
  - 组合输出保持 `homepage_projects` 兼容
- 前端：
  - 设置页可保存两类清单和时间窗口
  - 日报页分区展示正确

## 预期效果
- 日报只展示“近期更新”的项目
- 老牌必看与小项目明确分区
- 统计口径一致，无 14/16 误解
