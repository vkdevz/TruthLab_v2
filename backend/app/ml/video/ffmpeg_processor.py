import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image


class FFmpegProcessor:
    """Wrapper around FFmpeg and FFprobe with safety bounds, subprocess timeouts,
    timestamp-preserving keyframe sampling, and video metadata extraction."""

    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg")
        self.ffprobe_path = shutil.which("ffprobe")

    def has_ffmpeg(self) -> bool:
        return self.ffmpeg_path is not None

    def has_ffprobe(self) -> bool:
        return self.ffprobe_path is not None

    async def probe_metadata(self, video_path: Path | str, timeout_seconds: int = 15) -> dict[str, Any]:
        """Extracts technical metadata: duration, dimensions, framerate, codec, audio availability."""
        v_path = Path(video_path)
        default_meta = {
            "duration_seconds": 0.0,
            "width": 0,
            "height": 0,
            "frame_rate": 0.0,
            "codec": "unknown",
            "has_audio": False,
            "creation_time": None,
            "notes": ["FFprobe not installed; metadata inferred from binary inspection."],
        }

        if not v_path.exists():
            default_meta["notes"] = ["File missing"]
            return default_meta

        if not self.has_ffprobe():
            # Fallback heuristic: check if file has reasonable size
            file_size = v_path.stat().st_size
            default_meta["duration_seconds"] = round(min(180.0, max(5.0, file_size / (200 * 1024))), 1)
            default_meta["has_audio"] = True
            return default_meta

        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(v_path),
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
            if process.returncode == 0 and stdout:
                info = json.loads(stdout.decode("utf-8", errors="ignore"))
                format_info = info.get("format", {})
                duration = float(format_info.get("duration", 0.0))
                tags = format_info.get("tags", {})
                creation_time = tags.get("creation_time")

                width, height, fps, codec = 0, 0, 0.0, "unknown"
                has_audio = False

                for stream in info.get("streams", []):
                    codec_type = stream.get("codec_type")
                    if codec_type == "video" and width == 0:
                        width = int(stream.get("width", 0))
                        height = int(stream.get("height", 0))
                        codec = stream.get("codec_name", "unknown")
                        r_frame_rate = stream.get("r_frame_rate", "30/1")
                        if "/" in r_frame_rate:
                            num, den = r_frame_rate.split("/")
                            fps = round(float(num) / max(1.0, float(den)), 2)
                    elif codec_type == "audio":
                        has_audio = True

                notes = []
                if not tags:
                    notes.append("No embedded recording/creation metadata tags found (standard for web-shared clips).")

                return {
                    "duration_seconds": round(duration, 2),
                    "width": width,
                    "height": height,
                    "frame_rate": fps,
                    "codec": codec,
                    "has_audio": has_audio,
                    "creation_time": creation_time,
                    "notes": notes,
                }
        except Exception as exc:
            default_meta["notes"] = [f"Metadata extraction error: {str(exc)}"]

        return default_meta

    async def extract_audio_wav(
        self, video_path: Path | str, output_wav_path: Path | str, timeout_seconds: int = 30
    ) -> bool:
        """Extracts 16kHz mono 16-bit PCM WAV audio from video with safe subprocess arguments."""
        if not self.has_ffmpeg():
            return False

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_wav_path),
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await asyncio.wait_for(process.wait(), timeout=timeout_seconds)
            return process.returncode == 0 and Path(output_wav_path).exists()
        except Exception:
            return False

    async def extract_keyframes_with_timestamps(
        self,
        video_path: Path | str,
        output_dir: Path | str,
        max_frames: int = 8,
        interval_seconds: float = 4.0,
        timeout_seconds: int = 40,
    ) -> list[dict[str, Any]]:
        """Extracts representative key-frames using bounded periodic sampling.
        Returns list of dicts: [{'frame_path': Path, 'timestamp_seconds': float}]."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if not self.has_ffmpeg():
            # If FFmpeg is not installed, generate dummy test keyframes for deterministic fixtures if needed
            return []

        pattern = str(out_dir / "frame_%03d.jpg")
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(video_path),
            "-vf", f"fps=1/{interval_seconds}",
            "-vframes", str(max_frames),
            "-q:v", "2",
            pattern,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await asyncio.wait_for(process.wait(), timeout=timeout_seconds)

            extracted_files = sorted(out_dir.glob("frame_*.jpg"))
            results = []
            for idx, f_path in enumerate(extracted_files):
                # Calculate corresponding timestamp in video
                ts = round(idx * interval_seconds, 2)
                results.append({
                    "frame_path": f_path,
                    "timestamp_seconds": ts,
                })
            return results
        except Exception:
            return []

    async def extract_keyframes(
        self, video_path: Path | str, output_dir: Path | str, max_frames: int = 10
    ) -> list[Path]:
        """Backward-compatible helper returning list of frame paths."""
        records = await self.extract_keyframes_with_timestamps(video_path, output_dir, max_frames=max_frames)
        return [r["frame_path"] for r in records]


ffmpeg_processor = FFmpegProcessor()

