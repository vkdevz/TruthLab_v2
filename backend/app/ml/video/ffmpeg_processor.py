import asyncio
import os
from pathlib import Path
import shutil
import subprocess


class FFmpegProcessor:
    """Wrapper around FFmpeg binary with safety bounds, timeout limits, and fallbacks."""

    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg")

    def has_ffmpeg(self) -> bool:
        return self.ffmpeg_path is not None

    async def extract_audio_wav(self, video_path: Path | str, output_wav_path: Path | str, timeout_seconds: int = 30) -> bool:
        """Extracts 16kHz mono 16-bit PCM WAV audio from video."""
        if not self.has_ffmpeg():
            return False

        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-i", str(video_path),
            "-vn",  # Disable video stream
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_wav_path)
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            await asyncio.wait_for(process.wait(), timeout=timeout_seconds)
            return process.returncode == 0 and Path(output_wav_path).exists()
        except Exception:
            return False

    async def extract_keyframes(self, video_path: Path | str, output_dir: Path | str, max_frames: int = 10) -> list[Path]:
        """Extracts representative key-frames using I-frame filters or fixed intervals."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if not self.has_ffmpeg():
            return []

        # Extract 1 frame every 5 seconds, up to max_frames
        pattern = str(out_dir / "frame_%03d.jpg")
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(video_path),
            "-vf", "fps=1/5",
            "-vframes", str(max_frames),
            "-q:v", "2",
            pattern
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            await asyncio.wait_for(process.wait(), timeout=30)
            frames = sorted(out_dir.glob("frame_*.jpg"))
            return frames
        except Exception:
            return []


ffmpeg_processor = FFmpegProcessor()
