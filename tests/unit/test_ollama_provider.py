from engine.providers.ollama import OllamaProviderAdapter


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


def test_step_caps_output_tokens_via_num_predict(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["json"] = json
        return _FakeResponse({"message": {"content": "ok"}})

    monkeypatch.setattr("engine.providers.ollama.requests.post", fake_post)

    adapter = OllamaProviderAdapter(model="qwen2.5:7b", max_output_tokens=256)
    adapter.step("pergunta", tools=[], history=[])

    assert captured["json"]["options"]["num_predict"] == 256


def test_step_uses_default_output_token_cap(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["json"] = json
        return _FakeResponse({"message": {"content": "ok"}})

    monkeypatch.setattr("engine.providers.ollama.requests.post", fake_post)

    adapter = OllamaProviderAdapter(model="qwen2.5:7b")
    adapter.step("pergunta", tools=[], history=[])

    assert captured["json"]["options"]["num_predict"] == 512
