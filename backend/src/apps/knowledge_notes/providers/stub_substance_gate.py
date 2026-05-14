class StubSubstanceGateProvider:
    """Always returns 7 — all chunks pass in local dev and tests."""

    def assess(self, text: str) -> int:
        return 7
