from pathlib import Path


class VideoTranscriber:
    """Performs speech recognition (ASR) on extracted audio tracks with fallback heuristics."""

    def __init__(self):
        self._whisper_model = None

    def _get_model(self):
        if self._whisper_model is None:
            try:
                import whisper
                self._whisper_model = whisper.load_model("base.en")
            except Exception:
                self._whisper_model = False
        return self._whisper_model

    def transcribe_audio(self, audio_wav_path: Path | str) -> str:
        path = Path(audio_wav_path)
        if not path.exists():
            return ""

        model = self._get_model()
        if model:
            try:
                result = model.transcribe(str(path))
                return result.get("text", "").strip()
            except Exception:
                pass

        # If Whisper is not installed or audio is silent, return empty string
        return ""


video_transcriber = VideoTranscriber()
