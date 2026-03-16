# 日报排序（SOTA1：多目标打分 + MMR）设计

## 目标
- 日报排序以“信息价值/重要性”为核心，兼顾时效与证据质量
- 已读反馈影响未来 2 天内同项目排序（降权）
- 参数可配置、可随时调整

## 当前问题
- 排序只按重要度、更新时间和项目名，无法体现价值与多样性
- 已读反馈缺失，导致同项目反复占据头部

## 方案概览
采用**多目标打分 + MMR 多样性重排**。

流程：
1. 计算每个项目的 `base_score`
2. 应用“已读衰减”
3. 用 MMR 做多样性重排

## 评分模型
### 1) 重要度分数
- high = 1.0
- medium = 0.6
- low = 0.3

### 2) 时效分数
- 使用指数衰减
- `recency_score = exp(-age_days / recency_half_life_days)`

### 3) 证据质量分数
基于证据项中：
- `action_items` 数量
- `impact_points` 数量
- `detail_sections` 数量

归一化后合成：
- `evidence_score = min(1, 0.4*action + 0.3*impact + 0.3*details)`

### 4) 来源分数
- github_release = 1.0
- docs_feed = 0.7
- other = 0.5

### 5) 总分
`base_score = w_imp*importance + w_rec*recency + w_evi*evidence + w_src*source`

## 已读衰减
- 规则：**已读后 2 天内同项目降权**
- 公式：`base_score *= read_decay_factor`
- 默认 `read_decay_factor = 0.5`

## 多样性重排（MMR）
- 目标：避免相似项目/同来源/同标签挤满头部
- 相似度使用 Jaccard：
  - `tags`、`category`、`source` 作为多样性 key

MMR 公式：
`MMR = λ * score - (1-λ) * max_sim(selected, candidate)`

默认：`mmr_lambda = 0.7`

## 已读信号
- 默认：进入项目详情即“已读”
- 单用户存储，记录 `project_id / event_id / read_at`

## 数据结构
新增：`read_events.json`
```
[
  {"project_id": "kubernetes", "event_id": "...", "read_at": "2026-03-17T09:30:00Z"}
]
```

## 配置
新增 `daily_ranking` 配置，全部可调：
```
{
  "daily_ranking": {
    "weights": {
      "importance": 0.45,
      "recency": 0.25,
      "evidence": 0.20,
      "source": 0.10
    },
    "recency_half_life_days": 3,
    "read_decay_days": 2,
    "read_decay_factor": 0.5,
    "mmr_lambda": 0.7,
    "mmr_diversity_keys": ["source", "category", "tags"]
  }
}
```

## UI 行为
- 日报卡片可点击，进入项目页（专题库/项目详情）即记为已读
- 设置页提供参数配置

## 测试
- 已读 2 天内降权生效
- MMR 能拉开同类项目
- 参数调整后排序变化可观测

## 预期效果
- 同类项目不会长期霸榜
- 重要度仍是主排序，但价值感更强
- 已读反馈可持续起效
