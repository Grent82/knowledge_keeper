def get_embedding_provider():
    from django.conf import settings

    from .openai_embedding import OpenAICompatibleEmbeddingProvider

    return OpenAICompatibleEmbeddingProvider(
        base_url=settings.AI_HUB_BASE_URL,
        api_key=settings.AI_HUB_API_KEY,
        model=settings.AI_HUB_MODEL,
    )


def get_substance_gate_provider():
    from django.conf import settings

    from .openai_substance_gate import OpenAICompatibleSubstanceGateProvider

    return OpenAICompatibleSubstanceGateProvider(
        base_url=settings.AI_HUB_BASE_URL,
        api_key=settings.AI_HUB_API_KEY,
        model=settings.AI_HUB_MODEL,
    )
