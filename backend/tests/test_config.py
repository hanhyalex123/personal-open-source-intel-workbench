import os


def test_apply_runtime_network_defaults_forces_no_proxy(monkeypatch):
    from backend.config import apply_runtime_network_defaults

    monkeypatch.setenv("http_proxy", "http://127.0.0.1:7890")
    monkeypatch.setenv("https_proxy", "http://127.0.0.1:7890")
    monkeypatch.setenv("all_proxy", "socks5://127.0.0.1:7890")
    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)

    apply_runtime_network_defaults()

    assert os.environ["NO_PROXY"] == "*"
    assert os.environ["no_proxy"] == "*"


def test_load_environment_applies_runtime_network_defaults(monkeypatch):
    from backend.config import load_environment

    def fake_load_dotenv():
        os.environ["http_proxy"] = "http://127.0.0.1:7890"
        os.environ["https_proxy"] = "http://127.0.0.1:7890"
        os.environ["all_proxy"] = "socks5://127.0.0.1:7890"

    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)
    monkeypatch.setattr("backend.config.load_dotenv", fake_load_dotenv)

    load_environment()

    assert os.environ["NO_PROXY"] == "*"
    assert os.environ["no_proxy"] == "*"
