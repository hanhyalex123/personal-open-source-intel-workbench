import json

MAX_EVENT_BODY_CHARS = 3600


def build_analysis_prompt(event: dict) -> str:
    payload = json.dumps(_compact_event(event), ensure_ascii=False, indent=2)
    return f"""你是一个面向平台运维和基础设施团队的中文分析助手。

系统已经提前帮你做了一轮研究，事件里可能带有 `research_bundle`，里面会包含 changelog、官方文档、页面摘录和相关线索。你必须优先使用这些证据，不要只盯着 release body 或首页摘要。

请基于下面的上游事件，输出简洁但专业的中文分析，不要复述空话。重点说明：
1. 这次变化是什么
2. 引入了什么新技术、新能力或新方向
3. 哪些行为、配置、接口或升级路径发生了变化
4. 为什么对运维或平台团队重要
5. 影响范围与升级风险
6. 建议动作
7. 它是不是版本发布后的固定结论

你必须尽量提炼最具体的 1 到 3 个变化点，禁止只写“包含新特性、修复、安全补丁”这类空泛总结。
如果原文里出现了明确的网络、存储、API、升级、弃用、兼容性或安全变化，要优先把这些具体变化翻成中文并说清楚。
如果 GitHub release 本身很空，但 `research_bundle` 里有 changelog、文档或相关页面，你必须顺着这些证据写出更具体的结论。
如果证据仍然不足，要明确说“证据不足”，不要编造。

你必须只输出 JSON，不要输出额外解释。

JSON 字段要求：
- title_zh: 中文标题
- summary_zh: 中文一句话总结
- details_zh: 中文详细说明
- detail_sections: 数组，每项包含 title 和 bullets，用于结构化展示核心变化
- what_changed: 数组，列出最重要的变化
- new_technology: 数组，新引入的技术、能力或方向
- behavior_changes: 数组，行为变化、默认值变化或兼容性变化
- config_changes: 数组，配置、CLI、环境变量、接口或 schema 变化
- code_change_focus: 数组，涉及的核心模块、目录或组件
- docs_updates: 数组，关联文档更新点
- upgrade_risks: 数组，升级或落地风险
- future_direction: 数组，后续方向或演进趋势
- impact_scope: 影响范围
- impact_points: 数组，拆分后的影响点
- suggested_action: 建议动作
- action_items: 数组，拆分后的建议动作
- evidence: 数组，每项包含 title、url、snippet
- urgency: high / medium / low
- tags: 字符串数组
- is_stable: 布尔值，表示这是不是固定结论

事件数据：
{payload}
"""


def build_assistant_answer_prompt(*, query: str, filters: dict, local_evidence: list[dict], web_results: list[dict], answer_prompt: str = "") -> str:
    local_payload = json.dumps(local_evidence[:6], ensure_ascii=False, indent=2)
    web_payload = json.dumps(web_results[:4], ensure_ascii=False, indent=2)
    return f"""你是架构师开源情报站里的项目知识助手，面向个人技术提升。

请结合本地知识和实时网页结果回答用户问题。优先使用本地知识库；当本地知识不足时，再引用实时网页结果。
不要把来源网页中的自我介绍、产品名称或第一人称当成你自己的身份。

输出 JSON，字段如下：
- answer: 中文回答
- next_steps: 字符串数组

{answer_prompt}

用户问题：
{query}

筛选条件：
{json.dumps(filters, ensure_ascii=False, indent=2)}

本地知识：
{local_payload}

实时网页结果：
{web_payload}
"""


def build_project_daily_summary_prompt(*, project: dict, evidence_items: list[dict], summary_date: str) -> str:
    evidence_payload = json.dumps(evidence_items[:3], ensure_ascii=False, indent=2)
    return f"""你是架构师开源情报站的项目日报生成器。

请根据下面的项目证据，为首页生成一张“今日项目情报卡”。
目标不是罗列所有事件，而是用一句标题和一段总结告诉用户今天最值得关注的项目动向。

只输出 JSON，字段如下：
- headline: 字符串，格式尽量接近“项目名 今日重点：xxx”
- summary_zh: 字符串，一段简洁中文总结
- reason: 字符串，说明为什么今天值得看
- importance: high / medium / low

项目：
{json.dumps({"id": project.get("id"), "name": project.get("name")}, ensure_ascii=False, indent=2)}

日期：
{summary_date}

证据：
{evidence_payload}
"""


def _compact_event(event: dict) -> dict:
    compact = dict(event)
    body = compact.get("body", "")
    if isinstance(body, str) and len(body) > MAX_EVENT_BODY_CHARS:
        compact["body"] = f"{body[:MAX_EVENT_BODY_CHARS]}\n\n[truncated]"
    research_bundle = compact.get("research_bundle")
    if isinstance(research_bundle, dict):
        compact["research_bundle"] = _compact_nested_strings(research_bundle)
    return compact


def _compact_nested_strings(value):
    if isinstance(value, str):
        if len(value) > 2200:
            return f"{value[:2200]}\n\n[truncated]"
        return value
    if isinstance(value, list):
        return [_compact_nested_strings(item) for item in value[:10]]
    if isinstance(value, dict):
        return {key: _compact_nested_strings(item) for key, item in value.items()}
    return value
