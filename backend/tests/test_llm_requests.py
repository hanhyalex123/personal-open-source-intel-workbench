import json

import pytest
import requests


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class InvalidJsonResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def json(self):
        raise json.JSONDecodeError("Expecting value", self.text, 0)

    def raise_for_status(self):
        return None


class ErrorResponse:
    def __init__(self, status_code=503, text="upstream unavailable"):
        self.status_code = status_code
        self.text = text

    def json(self):
        return {}

    def raise_for_status(self):
        raise requests.exceptions.HTTPError(f"{self.status_code} Server Error")


def _sample_config():
    return {
        "active_provider": "packy",
        "reasoning_effort": "",
        "disable_response_storage": None,
        "packy": {
            "api_key": "primary-key",
            "api_url": "https://primary.example.com/v1/messages",
            "model": "claude-sonnet-4-6",
            "provider": "Packy",
            "protocol": "",
            "enabled": True,
        },
        "openai": {
            "api_key": "backup-key",
            "api_url": "https://backup.example.com/v1/responses",
            "model": "gpt-5.4",
            "provider": "OpenAI",
            "protocol": "openai-responses",
            "enabled": True,
        },
    }


def test_get_llm_settings_reads_local_gateway(monkeypatch):
    from backend.llm import get_llm_settings

    monkeypatch.setenv("PACKY_API_KEY", "gateway-key")
    monkeypatch.setenv("PACKY_API_URL", "http://127.0.0.1:8080/v1/messages")
    monkeypatch.setenv("PACKY_MODEL", "claude-sonnet-4-6")

    settings = get_llm_settings()

    assert settings["api_key"] == "gateway-key"
    assert settings["api_url"] == "http://127.0.0.1:8080/v1/messages"
    assert settings["model"] == "claude-sonnet-4-6"


def test_get_llm_settings_prefers_openai_when_only_openai_env_is_configured(monkeypatch):
    from backend.llm import get_llm_settings

    monkeypatch.delenv("PACKY_API_KEY", raising=False)
    monkeypatch.delenv("PACKY_API_URL", raising=False)
    monkeypatch.delenv("PACKY_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_API_URL", "https://code.swpumc.cn/v1/responses")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4")
    monkeypatch.setenv("OPENAI_PROTOCOL", "openai-responses")

    settings = get_llm_settings()

    assert settings["api_key"] == "openai-key"
    assert settings["api_url"] == "https://code.swpumc.cn/v1/responses"
    assert settings["model"] == "gpt-5.4"
    assert settings["protocol"] == "openai-responses"
    assert settings["provider"] == "OpenAI"


def test_get_llm_settings_switches_primary_provider_with_llm_config(monkeypatch):
    from backend.llm import get_llm_settings

    monkeypatch.setenv("PACKY_API_KEY", "gateway-key")
    monkeypatch.setenv("PACKY_API_URL", "http://127.0.0.1:8080/v1/messages")
    monkeypatch.setenv("PACKY_MODEL", "claude-sonnet-4-6")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    settings = get_llm_settings(
        {
            "active_provider": "openai",
            "reasoning_effort": "xhigh",
            "disable_response_storage": True,
            "packy": {
                "provider": "Packy",
            },
            "openai": {
                "provider": "OpenAI",
                "api_url": "https://code.swpumc.cn/v1/responses",
                "model": "gpt-5.4",
                "protocol": "openai-responses",
            },
        }
    )

    assert settings["api_key"] == "openai-key"
    assert settings["api_url"] == "https://code.swpumc.cn/v1/responses"
    assert settings["model"] == "gpt-5.4"
    assert settings["protocol"] == "openai-responses"
    assert settings["fallback_api_key"] == "gateway-key"
    assert settings["fallback_api_url"] == "http://127.0.0.1:8080/v1/messages"
    assert settings["fallback_model"] == "claude-sonnet-4-6"
    assert settings["reasoning_effort"] == "xhigh"
    assert settings["disable_response_storage"] is True


def test_get_llm_settings_skips_disabled_fallback_provider(monkeypatch):
    from backend.llm import get_llm_settings

    monkeypatch.delenv("PACKY_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    cfg = _sample_config()
    cfg["active_provider"] = "packy"
    cfg["openai"]["enabled"] = False

    settings = get_llm_settings(cfg)

    assert settings["fallback_api_key"] == ""
    assert settings["fallback_api_url"] == ""
    assert settings["fallback_model"] == ""
    assert settings["fallback_provider"] == ""
    assert settings["fallback_protocol"] == ""


def test_get_llm_settings_uses_enabled_openai_when_packy_disabled(monkeypatch):
    from backend.llm import get_llm_settings

    monkeypatch.delenv("PACKY_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    cfg = _sample_config()
    cfg["active_provider"] = "packy"
    cfg["packy"]["enabled"] = False
    cfg["openai"]["enabled"] = True

    settings = get_llm_settings(cfg)

    assert settings["provider"] == "OpenAI"
    assert settings["api_key"] == "backup-key"


def test_get_llm_settings_normalizes_openai_base_url(monkeypatch):
    from backend.llm import get_llm_settings

    monkeypatch.delenv("PACKY_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    cfg = _sample_config()
    cfg["active_provider"] = "openai"
    cfg["openai"]["api_url"] = "https://code.swpumc.cn"
    cfg["openai"]["protocol"] = ""

    settings = get_llm_settings(cfg)

    assert settings["api_url"] == "https://code.swpumc.cn/v1/responses"
    assert settings["protocol"] == "openai-responses"


def test_get_llm_settings_normalizes_openai_chat_url(monkeypatch):
    from backend.llm import get_llm_settings

    monkeypatch.delenv("PACKY_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    cfg = _sample_config()
    cfg["active_provider"] = "openai"
    cfg["openai"]["api_url"] = "https://code.swpumc.cn"
    cfg["openai"]["protocol"] = "openai-chat"

    settings = get_llm_settings(cfg)

    assert settings["api_url"] == "https://code.swpumc.cn/v1/chat/completions"
    assert settings["protocol"] == "openai-chat"


def test_parse_live_research_report_response_surfaces_error_message():
    from backend.llm import parse_live_research_report_response

    payload = {"code": "INVALID_API_KEY", "message": "Invalid API key"}
    result = parse_live_research_report_response(payload)

    assert "Invalid API key" in result["report_markdown"]


def test_analyze_event_raises_gateway_error_with_context(monkeypatch):
    from backend.llm import analyze_event

    def fake_post(url, headers=None, json=None, timeout=None):
        return ErrorResponse(status_code=503, text="upstream unavailable")

    monkeypatch.setenv("PACKY_API_KEY", "gateway-key")
    monkeypatch.setenv("PACKY_API_URL", "http://127.0.0.1:8080/v1/messages")
    monkeypatch.setenv("PACKY_MODEL", "claude-sonnet-4-6")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    with pytest.raises(RuntimeError) as exc_info:
        analyze_event(
            {
                "id": "github-release:kubernetes/kubernetes:v1.35.2",
                "source": "github_release",
                "repo": "kubernetes/kubernetes",
                "title": "v1.35.2",
                "version": "v1.35.2",
                "body": "See CHANGELOG",
                "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.2",
            }
        )

    message = str(exc_info.value)
    assert "http://127.0.0.1:8080/v1/messages" in message
    assert "claude-sonnet-4-6" in message
    assert "503" in message


def test_analyze_event_retries_once_on_read_timeout(monkeypatch):
    from backend.llm import analyze_event

    calls = {"count": 0}

    def fake_post(url, headers=None, json=None, timeout=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.exceptions.ReadTimeout("slow upstream")
        return DummyResponse(
            {
                "content": [
                    {
                        "type": "text",
                        "text": json_module.dumps(
                            {
                                "title_zh": "Kubernetes v1.35.2 补丁版本发布",
                                "summary_zh": "构建工具链升级到 Go 1.25.7。",
                                "details_zh": "这是一条具体结论。",
                                "impact_scope": "Kubernetes 构建与发布流程",
                                "suggested_action": "验证工具链兼容性。",
                                "urgency": "low",
                                "tags": ["kubernetes"],
                                "is_stable": True,
                            },
                            ensure_ascii=False,
                        ),
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setenv("PACKY_API_KEY", "test-key")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.35.2",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "v1.35.2",
            "version": "v1.35.2",
            "body": "See CHANGELOG",
            "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.2",
        }
    )

    assert calls["count"] == 2
    assert analysis["summary_zh"] == "构建工具链升级到 Go 1.25.7。"


def test_analyze_event_falls_back_to_backup_model_after_gateway_failure(monkeypatch):
    from backend.llm import analyze_event

    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "api_key": headers.get("x-api-key"), "model": json.get("model")})
        if len(calls) == 1:
            return ErrorResponse(status_code=503, text="gateway unavailable")
        return DummyResponse(
            {
                "content": [
                    {
                        "type": "text",
                        "text": json_module.dumps(
                            {
                                "title_zh": "Kubernetes v1.35.2 补丁版本发布",
                                "summary_zh": "已通过备用模型完成分析。",
                                "details_zh": "这是一条具体结论。",
                                "impact_scope": "Kubernetes 构建与发布流程",
                                "suggested_action": "验证工具链兼容性。",
                                "urgency": "low",
                                "tags": ["kubernetes"],
                                "is_stable": True,
                            },
                            ensure_ascii=False,
                        ),
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setenv("PACKY_API_KEY", "primary-key")
    monkeypatch.setenv("PACKY_API_URL", "http://127.0.0.1:8080/v1/messages")
    monkeypatch.setenv("PACKY_MODEL", "claude-sonnet-4-6")
    monkeypatch.setenv("OPENAI_API_KEY", "backup-key")
    monkeypatch.setenv("OPENAI_API_URL", "https://www.packyapi.com/v1/messages")
    monkeypatch.setenv("OPENAI_MODEL", "glm-5")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.35.2",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "v1.35.2",
            "version": "v1.35.2",
            "body": "See CHANGELOG",
            "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.2",
        }
    )

    assert len(calls) == 2
    assert calls[0]["url"] == "http://127.0.0.1:8080/v1/messages"
    assert calls[0]["model"] == "claude-sonnet-4-6"
    assert calls[1]["url"] == "https://www.packyapi.com/v1/messages"
    assert calls[1]["model"] == "glm-5"
    assert analysis["summary_zh"] == "已通过备用模型完成分析。"
    assert analysis["_llm"]["used_fallback"] is True
    assert analysis["_llm"]["model"] == "glm-5"


def test_analyze_event_uses_openai_protocol_when_chat_completions_url(monkeypatch):
    from backend.llm import analyze_event

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = json
        return DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(
                                {
                                    "title_zh": "Kubernetes v1.35.2 补丁版本发布",
                                    "summary_zh": "OpenAI 格式返回",
                                    "details_zh": "这是一条具体结论。",
                                    "impact_scope": "Kubernetes 构建与发布流程",
                                    "suggested_action": "验证工具链兼容性。",
                                    "urgency": "low",
                                    "tags": ["kubernetes"],
                                    "is_stable": True,
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setenv("PACKY_API_KEY", "openai-key")
    monkeypatch.setenv("PACKY_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
    monkeypatch.setenv("PACKY_MODEL", "claude-sonnet-4-6")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.35.2",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "v1.35.2",
            "version": "v1.35.2",
            "body": "See CHANGELOG",
            "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.2",
        }
    )

    assert captured["url"] == "http://127.0.0.1:8080/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer openai-key"
    assert "x-api-key" not in captured["headers"]
    assert analysis["summary_zh"] == "OpenAI 格式返回"


def test_analyze_event_uses_explicit_openai_protocol_on_nonstandard_url(monkeypatch):
    from backend.llm import analyze_event

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = json
        return DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(
                                {
                                    "title_zh": "Kubernetes v1.35.2 补丁版本发布",
                                    "summary_zh": "显式 protocol 生效",
                                    "details_zh": "这是一条具体结论。",
                                    "impact_scope": "Kubernetes 构建与发布流程",
                                    "suggested_action": "验证工具链兼容性。",
                                    "urgency": "low",
                                    "tags": ["kubernetes"],
                                    "is_stable": True,
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setenv("PACKY_API_KEY", "openai-key")
    monkeypatch.setenv("PACKY_API_URL", "https://gateway.example.com/llm")
    monkeypatch.setenv("PACKY_PROTOCOL", "openai-chat")
    monkeypatch.setenv("PACKY_MODEL", "gpt-5.4")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.35.2",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "v1.35.2",
            "version": "v1.35.2",
            "body": "See CHANGELOG",
            "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.2",
        }
    )

    assert captured["url"] == "https://gateway.example.com/llm"
    assert captured["headers"]["Authorization"] == "Bearer openai-key"
    assert "x-api-key" not in captured["headers"]
    assert "messages" in captured["payload"]
    assert analysis["summary_zh"] == "显式 protocol 生效"


def test_analyze_event_falls_back_to_text_response(monkeypatch):
    from backend.llm import analyze_event

    def fake_post(url, headers=None, json=None, timeout=None):
        return InvalidJsonResponse("纯文本回复")

    monkeypatch.setenv("PACKY_API_KEY", "test-key")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.35.3",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "v1.35.3",
            "version": "v1.35.3",
            "body": "See CHANGELOG",
            "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.3",
        }
    )

    assert analysis["summary_zh"] == "纯文本回复"
    assert analysis["analysis_mode"] == "fallback"


def test_analyze_event_reports_empty_body(monkeypatch):
    from backend.llm import analyze_event

    def fake_post(url, headers=None, json=None, timeout=None):
        return InvalidJsonResponse("")

    monkeypatch.setenv("PACKY_API_KEY", "test-key")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    with pytest.raises(RuntimeError) as exc_info:
        analyze_event(
            {
                "id": "github-release:kubernetes/kubernetes:v1.35.4",
                "source": "github_release",
                "repo": "kubernetes/kubernetes",
                "title": "v1.35.4",
                "version": "v1.35.4",
                "body": "See CHANGELOG",
                "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.4",
            }
        )

    assert "empty response body" in str(exc_info.value)


def test_analyze_event_uses_openai_responses_protocol(monkeypatch):
    from backend.llm import analyze_event

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = json
        return DummyResponse(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json_module.dumps(
                                    {
                                        "title_zh": "Incus 文档首读",
                                        "summary_zh": "Responses API 格式返回",
                                        "details_zh": "这是一条具体结论。",
                                        "impact_scope": "Incus 文档",
                                        "suggested_action": "阅读文档。",
                                        "urgency": "low",
                                        "tags": ["incus"],
                                        "is_stable": True,
                                    },
                                    ensure_ascii=False,
                                ),
                            }
                        ],
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setenv("PACKY_API_KEY", "openai-key")
    monkeypatch.setenv("PACKY_API_URL", "https://code.swpumc.cn/v1/responses")
    monkeypatch.setenv("PACKY_PROTOCOL", "openai-responses")
    monkeypatch.setenv("PACKY_MODEL", "gpt-5.4")
    monkeypatch.setenv("PACKY_REASONING_EFFORT", "xhigh")
    monkeypatch.setenv("PACKY_DISABLE_RESPONSE_STORAGE", "true")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "docs-feed:incus:docs:initial",
            "source": "docs_feed",
            "source_key": "incus:docs",
            "title": "Incus 文档",
            "body": "See docs",
            "url": "https://linuxcontainers.org/incus/docs/main/",
            "event_kind": "docs_initial_read",
        }
    )

    assert captured["url"] == "https://code.swpumc.cn/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer openai-key"
    assert captured["payload"]["input"].startswith("你是一个中文技术文档阅读助手")
    assert captured["payload"]["max_output_tokens"] == 1200
    assert captured["payload"]["reasoning_effort"] == "xhigh"
    assert captured["payload"]["store"] is False
    assert analysis["summary_zh"] == "Responses API 格式返回"


def test_analyze_event_falls_back_to_plain_text_summary_for_non_json_content(monkeypatch):
    from backend.llm import analyze_event

    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse(
            {
                "content": [
                    {
                        "type": "text",
                        "text": "temporary upstream html page",
                    }
                ]
            }
        )

    monkeypatch.setenv("PACKY_API_KEY", "test-key")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "docs-feed:kind:docs:network",
            "source": "docs_feed",
            "source_key": "kind:docs",
            "title": "kind 文档",
            "body": "See docs",
            "url": "https://kind.sigs.k8s.io/docs/",
            "event_kind": "docs_initial_read",
        }
    )

    assert analysis["analysis_mode"] == "fallback"
    assert "temporary upstream html page" in analysis["summary_zh"]


def test_analyze_event_uses_codex_protocol_with_responses_wire_format(monkeypatch):
    from backend.llm import analyze_event

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = json
        return DummyResponse(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json_module.dumps(
                                    {
                                        "title_zh": "Codex 通道返回",
                                        "summary_zh": "Codex 使用 Responses 格式返回",
                                        "details_zh": "这是一条具体结论。",
                                        "impact_scope": "Codex",
                                        "suggested_action": "保持观测。",
                                        "urgency": "low",
                                        "tags": ["codex"],
                                        "is_stable": True,
                                    },
                                    ensure_ascii=False,
                                ),
                            }
                        ],
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setenv("PACKY_API_KEY", "codex-key")
    monkeypatch.setenv("PACKY_API_URL", "https://codex-api-slb.packycode.com/v1")
    monkeypatch.setenv("PACKY_PROTOCOL", "codex")
    monkeypatch.setenv("PACKY_MODEL", "gpt-5.3-codex")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.35.2",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "v1.35.2",
            "version": "v1.35.2",
            "body": "See CHANGELOG",
            "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.2",
        }
    )

    assert captured["url"] == "https://codex-api-slb.packycode.com/v1"
    assert "input" in captured["payload"]
    assert "messages" not in captured["payload"]
    assert analysis["summary_zh"] == "Codex 使用 Responses 格式返回"


def test_analyze_event_rebuilds_fallback_payload_for_different_protocol(monkeypatch):
    from backend.llm import analyze_event

    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "payload": json})
        if len(calls) == 1:
            return ErrorResponse(status_code=503, text="gateway unavailable")
        return DummyResponse(
            {
                "content": [
                    {
                        "type": "text",
                        "text": json_module.dumps(
                            {
                                "title_zh": "Incus 文档更新",
                                "summary_zh": "fallback 已重建消息体",
                                "details_zh": "这是一条具体结论。",
                                "impact_scope": "Incus 文档",
                                "suggested_action": "阅读文档。",
                                "urgency": "low",
                                "tags": ["incus"],
                                "is_stable": True,
                            },
                            ensure_ascii=False,
                        ),
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setenv("PACKY_API_KEY", "primary-key")
    monkeypatch.setenv("PACKY_API_URL", "https://code.swpumc.cn/v1/responses")
    monkeypatch.setenv("PACKY_PROTOCOL", "openai-responses")
    monkeypatch.setenv("PACKY_MODEL", "gpt-5.4")
    monkeypatch.setenv("OPENAI_API_KEY", "backup-key")
    monkeypatch.setenv("OPENAI_API_URL", "https://www.packyapi.com/v1/messages")
    monkeypatch.setenv("OPENAI_MODEL", "glm-5")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "docs-feed:incus:docs:diff",
            "source": "docs_feed",
            "source_key": "incus:docs",
            "title": "Incus 文档",
            "body": "See docs",
            "url": "https://linuxcontainers.org/incus/docs/main/",
            "event_kind": "docs_diff_update",
        }
    )

    assert isinstance(calls[0]["payload"]["input"], str)
    assert calls[0]["payload"]["input"]
    assert calls[1]["url"] == "https://www.packyapi.com/v1/messages"
    assert calls[1]["headers"]["x-api-key"] == "backup-key"
    assert "input" not in calls[1]["payload"]
    assert "max_output_tokens" not in calls[1]["payload"]
    assert calls[1]["payload"]["messages"][0]["role"] == "user"
    assert calls[1]["payload"]["max_tokens"] == 1200
    assert analysis["summary_zh"] == "fallback 已重建消息体"


def test_analyze_event_uses_explicit_fallback_protocol_on_nonstandard_url(monkeypatch):
    from backend.llm import analyze_event

    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "payload": json})
        if len(calls) == 1:
            return ErrorResponse(status_code=503, text="gateway unavailable")
        return DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(
                                {
                                    "title_zh": "Kubernetes v1.35.2 补丁版本发布",
                                    "summary_zh": "显式 fallback protocol 生效",
                                    "details_zh": "这是一条具体结论。",
                                    "impact_scope": "Kubernetes 构建与发布流程",
                                    "suggested_action": "验证工具链兼容性。",
                                    "urgency": "low",
                                    "tags": ["kubernetes"],
                                    "is_stable": True,
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }
        )

    json_module = json
    monkeypatch.setenv("PACKY_API_KEY", "primary-key")
    monkeypatch.setenv("PACKY_API_URL", "http://127.0.0.1:8080/v1/messages")
    monkeypatch.setenv("PACKY_MODEL", "claude-sonnet-4-6")
    monkeypatch.setenv("OPENAI_API_KEY", "backup-key")
    monkeypatch.setenv("OPENAI_API_URL", "https://gateway.example.com/openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4")
    monkeypatch.setenv("OPENAI_PROTOCOL", "openai-chat")
    monkeypatch.setattr("backend.llm.requests.post", fake_post)

    analysis = analyze_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.35.2",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "v1.35.2",
            "version": "v1.35.2",
            "body": "See CHANGELOG",
            "url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.2",
        }
    )

    assert calls[1]["url"] == "https://gateway.example.com/openai/v1/chat/completions"
    assert calls[1]["headers"]["Authorization"] == "Bearer backup-key"
    assert "x-api-key" not in calls[1]["headers"]
    assert calls[1]["payload"]["messages"][0]["role"] == "user"
    assert analysis["summary_zh"] == "显式 fallback protocol 生效"
