from pathlib import Path

from django.conf import settings

from ..ports import SegmentResult, TranscriptionProvider, TranscriptionResult


class FasterWhisperProvider:
    def __init__(self, model_size: str, device: str, compute_type: str, model_dir: str) -> None:
        # Lazy-load the model on first use to avoid slow startup
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model_dir = model_dir or None
        self._model = None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
                download_root=self._model_dir,
            )
        return self._model

    def transcribe(self, audio_path: str, language: str = "") -> TranscriptionResult:
        # Resolve relative paths against MEDIA_ROOT
        path = Path(audio_path)
        if not path.is_absolute():
            path = Path(settings.MEDIA_ROOT) / path

        model = self._get_model()
        segments_iter, info = model.transcribe(
            str(path),
            language=language or None,
            beam_size=5,
        )

        segments = []
        full_text_parts = []
        for i, seg in enumerate(segments_iter, start=1):
            segments.append(
                SegmentResult(
                    sequence_number=i,
                    content=seg.text.strip(),
                    start_seconds=seg.start,
                    end_seconds=seg.end,
                )
            )
            full_text_parts.append(seg.text.strip())

        return TranscriptionResult(
            full_text=" ".join(full_text_parts),
            segments=segments,
            language_code=info.language,
        )


def make_faster_whisper_provider() -> TranscriptionProvider:
    return FasterWhisperProvider(
        model_size=getattr(settings, "WHISPER_MODEL_SIZE", "small"),
        device=getattr(settings, "WHISPER_DEVICE", "cpu"),
        compute_type=getattr(settings, "WHISPER_COMPUTE_TYPE", "int8"),
        model_dir=getattr(settings, "WHISPER_MODEL_DIR", ""),
    )
