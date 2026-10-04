from pathlib import Path
from typing import Any, Dict, List


class VideoTranscriber:
    """Performs speech recognition (ASR) on extracted audio tracks with timestamp preservation,
    modular interface, and fallback heuristics."""

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

    def transcribe(self, audio_wav_path: Path | str) -> dict[str, Any]:
        """Transcribes audio and returns full text plus timestamped segments."""
        path = Path(audio_wav_path)
        if not path.exists():
            return {"transcript": "", "segments": []}

        model = self._get_model()
        if model:
            try:
                result = model.transcribe(str(path))
                raw_text = result.get("text", "").strip()
                raw_segments = result.get("segments", [])

                segments = []
                for s in raw_segments:
                    segments.append({
                        "start": round(float(s.get("start", 0.0)), 2),
                        "end": round(float(s.get("end", 0.0)), 2),
                        "text": s.get("text", "").strip(),
                    })

                return {
                    "transcript": raw_text,
                    "segments": segments,
                }
            except Exception:
                pass

        # Fallback if Whisper is absent or audio is silent
        return {"transcript": "", "segments": []}

    def transcribe_audio(self, audio_wav_path: Path | str) -> str:
        """Backward-compatible helper returning transcript string only."""
        res = self.transcribe(audio_wav_path)
        return res.get("transcript", "")


video_transcriber = VideoTranscriber()

