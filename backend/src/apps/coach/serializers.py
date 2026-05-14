from rest_framework import serializers


class HistoryEntrySerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant"])
    content = serializers.CharField(allow_blank=False, trim_whitespace=True)


class CoachChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField(allow_blank=False, trim_whitespace=True)
    context_tag = serializers.CharField(required=False, allow_blank=True, default="")
    history = HistoryEntrySerializer(many=True, required=False)

    def validate_question(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("This field may not be blank.")
        return normalized

    def validate_history(self, value: list[dict[str, str]]) -> list[dict[str, str]]:
        return value[-5:]
