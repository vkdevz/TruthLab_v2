# Image Intelligence Pipeline

## 1. Overview
The Image Intelligence module provides automated extraction, forensic analysis, text digitization (OCR), and claim extraction from image media (`image/jpeg`, `image/png`, `image/webp`).

Images undergo a multi-stage analysis pipeline that separates **factual claim verification** from **probabilistic media forensic signals**.

```
IMAGE UPLOAD
     │
     ├── Ingestion & Magic Byte Validation
     │
     ├── Metadata & EXIF Analysis ──> [Dimensions, Color, Camera, C2PA Provenance]
     │
     ├── Error Level Analysis (ELA) ──> [Recompression Error, Tampering Heuristic]
     │
     ├── Synthetic Media Detector ──> [Probabilistic AI-Generation Score]
     │
     └── OCR Engine & Text Normalizer ──> [Extracted Text, Bounding Regions]
              │
              ▼ (if text present)
       Unified Corpus ──> Claim Extraction ──> Evidence Retrieval ──> Verification
```

---

## 2. Core Components

### 2.1 Metadata & Provenance Forensics (`metadata_forensics.py`)
- **Metadata Fields Extracted**:
  - Image dimensions (`width`, `height`, aspect ratio)
  - Color mode (`RGB`, `RGBA`, `CMYK`, `L`)
  - Image format (`JPEG`, `PNG`, `WEBP`)
  - Timestamp tags (`DateTimeOriginal`, `DateTimeDigitized`, `DateTime`)
  - Camera & Hardware tags (`Make`, `Model`, `Software`)
  - Digital Provenance (`C2PA` manifest indicators / metadata markers)
- **Forensic Principle**:
  - **Missing EXIF is NOT proof of manipulation**. Popular social networks (Twitter/X, Facebook, WhatsApp, Telegram) routinely strip EXIF metadata during compression. Absence of EXIF is explicitly documented as standard social media behavior.

### 2.2 Error Level Analysis (ELA) (`ela_forensics.py`)
- **Methodology**:
  - Computes error differences between the source image and a controlled recompressed copy at 90% JPEG quality.
  - Calculates per-block statistics: `mean_error`, `std_error`, `max_error`, and anomalous high-error block ratio (`ratio_anomalous_blocks`).
- **Forensic Signal**:
  - Emits a structured `manipulation_signal`:
    - `score` (0.0 to 1.0)
    - `interpretation` (e.g., "Consistent compression profile across blocks" vs "Localized variance peaks detected")
    - `limitations` ("Heuristic indicator only; compression artifacts, resaving, or social-media re-encoding can trigger false positives").
  - **Rule**: ELA is never reported as definitive proof of forgery.

### 2.3 Synthetic / AI-Generated Media Detector (`synthetic_detector.py`)
- **Interface**: `SyntheticMediaDetector` (Abstract Base Class).
- **Default Concrete Implementation**: `HeuristicFrequencySyntheticDetector` (v1.2.0).
- **Signals Examined**:
  - Normalized channel saturation dispersion (diffusion models frequently exhibit distinctive high-saturation profiles)
  - Laplacian gradient variance (proxy for unnatural edge sharpness or ultra-smoothed diffusion textures)
- **Model Output**:
  - `model_name`: `"HeuristicFrequencySyntheticDetector"`
  - `model_version`: `"1.2.0"`
  - `preprocessing`: `"RGB normalization, Laplacian gradient variance, saturation spread"`
  - `synthetic_probability`: Continuous probability float in `[0.05, 0.95]`
  - `confidence`: Qualitative confidence (`"LOW"`, `"MEDIUM"`, `"HIGH"`)
  - `limitations`: Explicit uncertainty disclosure ("Heuristic signal only; not benchmarked against unseen generative models; do not treat as ground-truth AI detection").

### 2.4 OCR Engine & Text Normalizer (`ocr_engine.py`)
- **Text Extraction**:
  - Integrates `pytesseract` if system binary is available.
  - Implements an automated local image processing fallback (detects high-contrast text regions and synthetic font stamps).
- **Normalized Output Schema**:
  ```json
  {
    "text": "Extracted normalized text...",
    "confidence": 0.88,
    "regions": [
      {"box": [10, 20, 300, 80], "text": "Headline text", "confidence": 0.92}
    ]
  }
  ```
- **Text Normalization**:
  - Cleans excessive whitespace, line breaks, and trailing punctuation.
  - Fixes spaced-out capital letters from poster titles (e.g., `"B R E A K I N G"` -> `"BREAKING"`).

---

## 3. Claim Routing & Insufficient Evidence Gate
- **Image with Text**:
  - Extracted normalized text enters the standard claim extraction pipeline (`claim_decomposer`).
  - Extracted claims are matched against external evidence and routed to late multimodal fusion.
- **Image without Legible Text**:
  - When an image contains scenery, portraits, or memes without testable statements, the system returns `INSUFFICIENT_EVIDENCE`.
  - Forensic indicators are preserved and displayed, but factual claims are never fabricated.

---

## 4. Limitations
1. Heuristic synthetic probability is an uncalibrated proxy signal.
2. OCR quality depends on image resolution, contrast, and font stylization.
3. ELA does not detect lossless manipulations or sophisticated inpainting.
