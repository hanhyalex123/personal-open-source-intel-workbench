# LLM 路由与控制台改版设计

## 目标

解决研究报告/事件分析中的“模型返回空响应”不可观测问题；为同步、日报、研究建立统一的 LLM 路由器；支持同一 OpenAI 网关下的多模型/多 key 降级；当主模型与备用模型均不可用时，直接中止 job，避免继续爬虫和白跑分析；同时将设置页改造成更接近阿里云控制台风格。

## 已确认规则

- 主路由优先：`gpt-5.4`
- 失败降级：`gpt-5.2`
- 若 `gpt-5.4` 与 `gpt-5.2` 都不可用：
  - 明确告警
  - 当前同步/日报/研究任务直接失败
  - 不继续做后续爬虫与分析
- 日报、研究报告、同步日志中要体现本次实际使用的模型
- 前端设置页改为更规整的控制台风格，而不是现在的散乱白板表单

## 根因结论

当前“空响应”并不完全是解析逻辑错误：

1. 历史空响应记录主要来自 `OpenAI / gpt-5.2 / https://code.swpumc.cn`，属于历史运行结果。
2. 当前真实研究报告主链路可以成功返回，说明链路并非持续性损坏。
3. 直接对网关做最小 `/v1/responses` 测试时，`gpt-5.4` 与 `gpt-5.2` 均返回 `503 Service temporarily unavailable`，说明需要在应用层加入 preflight 和硬门禁，而不是继续让 job 盲跑。
4. 当前系统缺少：
   - 统一路由器
   - key/model 级别的健康探测
   - job 开始前的 preflight
   - 调用元信息落库与前端展示
   - “部分成功/明确失败”的标准化状态

## 方案概述

### 1. 统一 LLM 路由器

新增一个统一的路由层，负责：

- 读取 LLM 配置中的多条 OpenAI 路由项
- 按优先级选择 `gpt-5.4`
- 失败时自动切到 `gpt-5.2`
- 记录实际使用：
  - provider
  - model
  - route alias / key alias
  - 是否降级
  - 失败原因

这层将被以下入口复用：

- 事件分析 `analyze_event`
- 日报摘要 `summarize_project_daily_intel`
- 研究报告 `generate_live_research_report`
- 助手回答 `answer_question_with_context`

### 2. Job 前置 preflight

在以下任务启动前先做最小模型探活：

- 手动同步
- 定时同步
- 手动日报
- 定时日报
- 研究报告请求

preflight 规则：

- 先测 `gpt-5.4`
- 再测 `gpt-5.2`
- 若两个都失败：返回结构化错误并中止任务

对于同步 job：

- preflight 失败后，不发起任何 source crawl
- job 状态直接为 failed
- `message` 写明 `LLM 不可用，已中止同步`

### 3. 同步成功判定收紧

将来源和分析状态拆开记录：

- source fetch status: `success / partial / failed / timeout / blocked`
- analysis status: `success / failed / skipped / blocked`

关键变化：

- 当 job 因 LLM preflight 失败被拦截时，来源状态记为 `blocked`
- 前端同步日志页可区分“没抓到”与“未开始抓，因为模型不可用”

### 4. 调用元信息展示

把 `_llm` 元信息扩展为：

- provider
- model
- route_alias
- api_url
- used_fallback
- fallback_from_provider
- fallback_from_model
- fallback_reason
- preflight_checked

并在以下位置展示：

- 日报项目卡/日报详情：`本次模型`
- 研究报告页：`生成模型`
- 同步日志详情：`模型链路`

### 5. 配置模型改造

现有 `llm.openai` 为单路由结构。需要演进成：

- 保留兼容旧字段
- 新增 `routes` 数组

示例：

```json
{
  "llm": {
    "active_provider": "openai",
    "strategy": "ordered-failover",
    "openai": {
      "enabled": true,
      "routes": [
        {
          "alias": "primary-gpt54",
          "api_key": "...",
          "api_url": "https://code.swpumc.cn",
          "model": "gpt-5.4",
          "protocol": "openai-responses",
          "priority": 1,
          "enabled": true
        },
        {
          "alias": "fallback-gpt52",
          "api_key": "...",
          "api_url": "https://code.swpumc.cn",
          "model": "gpt-5.2",
          "protocol": "openai-responses",
          "priority": 2,
          "enabled": true
        }
      ]
    }
  }
}
```

### 6. 前端改版方向

设置页采用阿里云控制台风格：

- 分区更明确
- 基础配置和高级配置分层
- 大块白底表单改为卡片式控制台布局
- 复选框改为开关样式
- 模型页显示：
  - 路由策略
  - 主模型
  - 备用模型
  - 最近探活结果
  - 路由表
- 助手页分三块：
  - 默认范围
  - 检索策略
  - Prompt

## 错误处理策略

### LLM 层

- `503 / 5xx / network timeout`：允许降级到下一个 route
- `429`：允许降级到下一个 route
- `4xx 配置错误（如 key 无效）`：允许切换到下一个 route，但要保留明确错误
- 全部失败：抛出结构化 `LLMRequestError`

### Job 层

- preflight 失败：job 直接 failed
- 不做 source crawl
- 不做分析
- 不产出日报

### 前端层

- 不再默认显示“模型返回空响应”这种无上下文文案
- 改成：
  - `研究报告生成失败`
  - `主模型 gpt-5.4 不可用，备用模型 gpt-5.2 也不可用`
  - 可展开看详情

## 测试策略

### 后端

- 路由优先顺序测试
- 5.4 失败后自动切 5.2 测试
- 两个都失败时 job 中止测试
- preflight 失败时同步不启动任何 source 测试
- `_llm` 元信息写入分析/报告测试

### 前端

- 模型设置页渲染新路由表
- 助手页渲染新分组布局
- 报告页显示模型信息
- 同步失败页显示 blocked/LLM preflight failed

## 非目标

- 本轮不做多网关负载均衡
- 本轮不做复杂加权策略
- 本轮不做收藏/个性化推荐系统扩展
