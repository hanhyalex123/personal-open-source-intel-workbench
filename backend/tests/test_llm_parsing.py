def test_prompt_contains_required_chinese_analysis_instructions():
    from backend.prompts import build_analysis_prompt

    prompt = build_analysis_prompt(
        {
            "id": "github-release:kubernetes/kubernetes:v1.31.0",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "Kubernetes v1.31.0",
            "version": "v1.31.0",
            "body": "Kubernetes 1.31 recommends nftables mode.",
            "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.31.0",
            "research_bundle": {
                "release": {"version": "v1.31.0"},
                "changelog": {"version_section": "# v1.31.0\n\n### Feature\n- recommend nftables"},
            },
        }
    )

    assert "中文" in prompt
    assert "运维" in prompt
    assert "固定结论" in prompt
    assert "JSON" in prompt
    assert "最具体" in prompt
    assert "detail_sections" in prompt
    assert "action_items" in prompt
    assert "research_bundle" in prompt
    assert "what_changed" in prompt
    assert "new_technology" in prompt
    assert "config_changes" in prompt
    assert "future_direction" in prompt
    assert "evidence" in prompt


def test_prompt_truncates_large_body_payload():
    from backend.prompts import build_analysis_prompt

    prompt = build_analysis_prompt(
        {
            "id": "docs-feed:k8s-zh-docs-home:https://kubernetes.io/zh-cn/docs/home/",
            "source": "docs_feed",
            "title": "Kubernetes 中文文档首页",
            "body": "A" * 12000,
            "url": "https://kubernetes.io/zh-cn/docs/home/",
        }
    )

    assert len(prompt) < 9000
    assert "A" * 5000 not in prompt


def test_parse_analysis_response_reads_structured_json():
    from backend.llm import parse_analysis_response

    analysis = parse_analysis_response(
        {
            "content": [
                {
                    "type": "text",
                    "text": """{
  "title_zh": "Kubernetes 1.31 网络推荐更新",
  "summary_zh": "Kubernetes 1.31 推荐使用 nftables 路径。",
  "details_zh": "这是面向运维团队的稳定版本结论。",
  "detail_sections": [{"title": "核心变化点", "bullets": ["推荐使用 nftables"]}],
  "what_changed": ["kube-proxy 推荐使用 nftables 路径"],
  "new_technology": ["nftables 模式"],
  "behavior_changes": ["网络规则编排路径发生变化"],
  "config_changes": ["需要确认底层内核和插件支持 nftables"],
  "code_change_focus": ["kube-proxy", "节点网络配置"],
  "docs_updates": ["网络模式文档同步更新"],
  "upgrade_risks": ["旧 iptables 预设可能需要复核"],
  "future_direction": ["网络栈逐步向 nftables 路径收敛"],
  "evidence": [{"title": "CHANGELOG", "url": "https://example.com/changelog", "snippet": "recommend nftables"}],
  "impact_scope": "Kubernetes 网络插件与节点网络配置",
  "impact_points": ["Kubernetes 网络插件与节点网络配置"],
  "suggested_action": "检查当前插件和内核能力，评估切换路径。",
  "action_items": ["检查当前插件和内核能力，评估切换路径。"],
  "urgency": "medium",
  "tags": ["kubernetes", "networking", "nftables"],
  "is_stable": true
}""",
                }
            ]
        }
    )

    assert analysis["title_zh"] == "Kubernetes 1.31 网络推荐更新"
    assert analysis["is_stable"] is True
    assert analysis["tags"] == ["kubernetes", "networking", "nftables"]
    assert analysis["detail_sections"][0]["title"] == "核心变化点"
    assert analysis["detail_sections"][0]["bullets"][0] == "推荐使用 nftables"
    assert analysis["what_changed"] == ["kube-proxy 推荐使用 nftables 路径"]
    assert analysis["future_direction"] == ["网络栈逐步向 nftables 路径收敛"]
    assert analysis["evidence"][0]["title"] == "CHANGELOG"
    assert analysis["impact_points"] == ["Kubernetes 网络插件与节点网络配置"]
    assert analysis["action_items"] == ["检查当前插件和内核能力，评估切换路径。"]


def test_parse_analysis_response_handles_markdown_json_fence():
    from backend.llm import parse_analysis_response

    analysis = parse_analysis_response(
        {
            "content": [
                {
                    "type": "text",
                    "text": """```json
{
  "title_zh": "文档建议更新",
  "summary_zh": "文档侧补充了新建议。",
  "details_zh": "这是可直接展示的中文分析。",
  "impact_scope": "文档使用者",
  "suggested_action": "同步内部知识库。",
  "urgency": "low",
  "tags": ["docs"],
  "is_stable": false
}
```""",
                }
            ]
        }
    )

    assert analysis["summary_zh"] == "文档侧补充了新建议。"


def test_parse_analysis_response_repairs_unescaped_quotes_inside_strings():
    from backend.llm import parse_analysis_response

    analysis = parse_analysis_response(
        {
            "content": [
                {
                    "type": "text",
                    "text": """```json
{
  "title_zh": "Kubernetes v1.31.0 正式发布",
  "summary_zh": "Kubernetes 1.31 主版本发布，包含安全修复",
  "details_zh": "存在"紧急升级注意事项"，升级前必读",
  "impact_scope": "所有 Kubernetes 集群",
  "suggested_action": "先看变更，再升级",
  "urgency": "high",
  "tags": ["kubernetes", "upgrade"],
  "is_stable": true
}
```""",
                }
            ]
        }
    )

    assert analysis["details_zh"] == '存在"紧急升级注意事项"，升级前必读'


def test_parse_analysis_response_derives_structured_fields_from_legacy_strings():
    from backend.llm import parse_analysis_response

    analysis = parse_analysis_response(
        {
            "content": [
                {
                    "type": "text",
                    "text": """{
  "title_zh": "Kubernetes v1.31.0 正式发布",
  "summary_zh": "Kubernetes 发布 v1.31.0 版本。",
  "details_zh": "**核心变化点：**\\n\\n1. **安全修复**\\n   - 修复 A\\n   - 修复 B\\n\\n2. **API 变更**\\n   - 变更 C",
  "impact_scope": "控制平面；节点组件；Windows 节点",
  "suggested_action": "1. 先看 CHANGELOG\\n2. 在测试环境验证\\n3. 再安排升级",
  "urgency": "high",
  "tags": ["kubernetes"],
  "is_stable": true
}""",
                }
            ]
        }
    )

    assert analysis["detail_sections"][0]["title"] == "安全修复"
    assert analysis["detail_sections"][0]["bullets"] == ["修复 A", "修复 B"]
    assert analysis["detail_sections"][1]["title"] == "API 变更"
    assert analysis["impact_points"] == ["控制平面", "节点组件", "Windows 节点"]
    assert analysis["action_items"] == ["先看 CHANGELOG", "在测试环境验证", "再安排升级"]


def test_parse_analysis_response_repairs_trailing_commas_and_prose():
    from backend.llm import parse_analysis_response

    payload = {
        "content": [
            {
                "type": "text",
                "text": "Here is the result:\n```json\n{\n  \"title_zh\": \"t\",\n  \"summary_zh\": \"s\",\n  \"impact_scope\": \"scope\",\n  \"suggested_action\": \"act\",\n  \"urgency\": \"low\",\n  \"tags\": [\"k\"],\n  \"is_stable\": true,\n}\n```",
            }
        ]
    }
    parsed = parse_analysis_response(payload)
    assert parsed["title_zh"] == "t"


def test_parse_analysis_response_repairs_unterminated_string():
    from backend.llm import parse_analysis_response

    payload = {
        "content": [
            {
                "type": "text",
                "text": "{\n  \"title_zh\": \"t\",\n  \"summary_zh\": \"s\",\n  \"impact_scope\": \"scope\",\n  \"suggested_action\": \"act\",\n  \"urgency\": \"low\",\n  \"tags\": [\"k\"],\n  \"is_stable\": true,\n  \"details_zh\": \"missing end\n",
            }
        ]
    }
    parsed = parse_analysis_response(payload)
    assert parsed["summary_zh"] == "s"
