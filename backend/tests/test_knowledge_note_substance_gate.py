from apps.knowledge_notes.providers.openai_substance_gate import (
    OpenAICompatibleSubstanceGateProvider,
)


def test_substance_gate_disables_qwen_thinking_mode():
    captured: dict[str, object] = {}

    class DummyCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)

            class Message:
                content = "7"
                model_extra = {}

            class Choice:
                message = Message()
                model_extra = {}

            class Response:
                choices = [Choice()]

            return Response()

    class DummyChat:
        completions = DummyCompletions()

    provider = OpenAICompatibleSubstanceGateProvider(
        "https://example.com", "test-key", "test-model"
    )
    provider._client = type("DummyClient", (), {"chat": DummyChat()})()

    score = provider.assess("Kurzer Abschnitt")

    assert score == 7
    assert captured["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
