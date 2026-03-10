import json

import requests


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


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
