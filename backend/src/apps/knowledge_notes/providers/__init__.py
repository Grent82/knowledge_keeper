from django.conf import settings


def get_embedding_provider():
    provider = getattr(settings, "EMBEDDING_PROVIDER", "stub")
    if provider == "openai_compatible":
        from .openai_embedding import OpenAICompatibleEmbeddingProvider

        return OpenAICompatibleEmbeddingProvider()
    from .stub_embedding import StubEmbeddingProvider

    return StubEmbeddingProvider()


def get_substance_gate_provider():
    provider = getattr(settings, "SUBSTANCE_GATE_PROVIDER", "stub")
    if provider == "openai_compatible":
        from .openai_substance_gate import OpenAICompatibleSubstanceGateProvider

        return OpenAICompatibleSubstanceGateProvider()
    from .stub_substance_gate import StubSubstanceGateProvider

    return StubSubstanceGateProvider()
