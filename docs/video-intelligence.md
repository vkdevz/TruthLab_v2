# Video Intelligence Pipeline

## 1. Overview
The Video Intelligence module processes video files (`video/mp4`, `video/webm`, `video/quicktime`), extracting both speech transcripts and visual keyframe content to build a unified textual corpus for factual claim verification.

```
VIDEO UPLOAD
     │
     ├── Ingestion & Magic Byte Validation (MP4, WebM, QuickTime)
     │
     ├── FFmpeg Technical Metadata Probe ──> [Duration, Codec, Dimensions, FPS, Audio Stream]
     │
     ├── Audio Extraction & ASR Transcription ──> [Timestamped Dialogue Segments]
     │
     ├── Bounded Keyframe Sampling ──> [Timestamped Frame Images]
     │         │
     │         ▼
     │   Keyframe OCR & Visual Forensics ──> [Overlay Text, Frame ELA, Frame Synthetic Prob]
     │
     └── Combined Corpus ──> Claim Extraction ──> Evidence Retrieval ──> Temporal Verification ──> Verdict
```

---

## 2. Core Components

### 2.1 Video Technical Probe (`ffmpeg_processor.py`)
- **Metadata Fields Extracted**:
  - `duration_seconds`: Total runtime in seconds (enforcing max duration limit of 300 seconds)
  - `dimensions`: Width and height (e.g. 1920x1080)
  - `fps`: Frame rate
  - `codec`: Video compression format (e.g. h264, vp9, hevc)
  - `has_audio`: Boolean presence of audio stream
  - `creation_time`: Container-level creation timestamp
- **Safety**:
  - Safe argument vector execution (no shell interpolation).
  - Explicit timeouts (15 seconds) preventing hanging subprocesses.
  - Resource limit checking rejecting oversized files (>100MB) or excessive durations (>5 minutes).

### 2.2 Speech-to-Text Transcription (`transcriber.py`)
- **ASR Interface**: `VideoTranscriber` (Abstract Base Class).
- **Default Concrete Implementation**: `WhisperTranscriber`.
  - Integrates OpenAI's `whisper` (`base.en`) when installed.
  - Provides deterministic local fallback for resource-constrained or headless environments.
- **Output Schema**:
  ```json
  {
    "transcript": "Full concatenated speech transcript...",
    "segments": [
      {"start": 0.0, "end": 4.5, "text": "Officials reported a massive flood downtown"},
      {"start": 4.6, "end": 9.2, "text": "Rescue teams were deployed immediately"}
    ]
  }
  ```
- **Timestamp Preservation**: All dialogue segments retain seconds-level start and end timestamps.

### 2.3 Adaptive Keyframe Extraction & Scene OCR (`scene_extractor.py`)
- **Keyframe Extraction**:
  - Bounded periodic and scene-change sampling.
  - Samples keyframes at bounded intervals (default: 4.0s interval, maximum 6 keyframes).
  - Preserves exact timestamp offsets for each extracted frame.
- **Keyframe Processing**:
  - For each extracted frame:
    - Runs OCR with confidence and bounding boxes to extract onscreen tickers, chyrons, and captions.
    - Runs ELA and synthetic media heuristics.
  - Concatenates unique overlay text with speech transcripts.

---

## 3. Video Factual Verification vs Deepfake Detection
### Important Distinction
This system performs **video-based factual and misinformation verification**:
- Grounding claims from dialogue and on-screen overlays against authoritative external evidence.
- Verifying temporal consistency between video content and current events.
- Assessing cross-modal alignment between video audio, visual text, and the claim.

**It does NOT constitute definitive deepfake detection.**
- Facial manipulation / GAN / diffusion deepfake detection requires specialized per-frame face tracking models (e.g. MesoNet, Xception-FaceForensics++) trained on comprehensive deepfake datasets.
- Forensic indicators reported on keyframes are lightweight heuristics with stated uncertainty.

---

## 4. Resource Limits & Security
- Maximum video size: 100 MB.
- Maximum duration: 300 seconds (5 minutes).
- Maximum sampled keyframes: 6 frames per video.
- All temporary keyframes and audio tracks are stored in isolated scratch directories and cleaned up on job completion.
