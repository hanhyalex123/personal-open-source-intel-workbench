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


class ErrorResponse:
    def __init__(self, status_code=503, text="upstream unavailable"):
        self.status_code = status_code
        self.text = text

    def json(self):
        return {}

    def raise_for_status(self):
        raise requests.exceptions.HTTPError(f"{self.status_code} Server Error")


def test_get_llm_settings_reads_local_gateway(monkeypatch):
    from backend.llm import get_llm_settings

    monkeypatch.setenv("PACKY_API_KEY", "gateway-key")
    monkeypatch.setenv("PACKY_API_URL", "http://127.0.0.1:8080/v1/messages")
    monkeypatch.setenv("PACKY_MODEL", "claude-sonnet-4-6")

    settings = get_llm_settings()

    assert settings["api_key"] == "gateway-key"
    assert settings["api_url"] == "http://127.0.0.1:8080/v1/messages"
    assert settings["model"] == "claude-sonnet-4-6"


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
    monkeypatch.setenv("LLM_FALLBACK_API_KEY", "backup-key")
    monkeypatch.setenv("LLM_FALLBACK_API_URL", "https://www.packyapi.com/v1/messages")
    monkeypatch.setenv("LLM_FALLBACK_MODEL", "glm-5")
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
