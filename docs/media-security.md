# Media Ingestion & Execution Security

## 1. Overview
Processing untrusted user-uploaded media (images and videos) exposes verification systems to major security attack vectors, including zip bombs, shell injection via media filenames, buffer overflows in media codecs, and Server-Side Request Forgery (SSRF).

The media ingestion layer in `backend/app/services/storage.py` and execution modules enforce strict multi-layered defenses.

---

## 2. Ingestion Defense Layers

### 2.1 File Extension & MIME Validation
- **Image Extensions**: `.jpg`, `.jpeg`, `.png`, `.webp`
- **Image MIMEs**: `image/jpeg`, `image/png`, `image/webp`
- **Video Extensions**: `.mp4`, `.webm`, `.mov`, `.avi`, `.mkv`
- **Video MIMEs**: `video/mp4`, `video/webm`, `video/quicktime`, `video/x-msvideo`, `video/x-matroska`

### 2.2 Magic Byte Signature Inspection (`validate_magic_bytes`)
MIME headers and file extensions can be trivially spoofed by attackers. The storage service inspects the leading bytes of every upload stream before persisting to disk:
- **JPEG**: Leading `\xFF\xD8\xFF`
- **PNG**: Leading `\x89PNG\r\n\x1a\n`
- **WebP**: `RIFF....WEBP` header
- **MP4 / MOV**: `ftyp`, `moov`, `wide`, or `mdat` within the initial 32 bytes
- **WebM / MKV**: `\x1A\x45\xDF\xA3` EBML container header
- **AVI**: `RIFF` container header

Any file with a mismatched signature is rejected with `HTTP 400 Bad Request`.

### 2.3 Filename Sanitization & Path Traversal Prevention
- User filenames are never used directly as filesystem paths.
- Filenames are sanitized via `re.sub(r"[^a-zA-Z0-9_\-\.]", "_", Path(filename).name)`.
- Files on disk are assigned cryptographic UUIDv4 filenames: `{uuid4}{sanitized_extension}` in a dedicated uploads directory.

### 2.4 Streaming Resource Limits
Uploads are read in bounded 64KB chunks:
- Max image size: **15 MB** (`MAX_IMAGE_SIZE_BYTES`)
- Max video size: **100 MB** (`MAX_VIDEO_SIZE_BYTES`)
If a stream exceeds the threshold, disk writing terminates immediately and `HTTP 413 Payload Too Large` is returned.

---

## 3. Subprocess & Media Processing Security

### 3.1 Subprocess Argument Arrays (No Shell Interpolation)
- Commands invoking external tools (`ffmpeg`, `ffprobe`, `tesseract`) are strictly executed using parameter arrays:
  ```python
  # SAFE:
  args = ["ffmpeg", "-y", "-i", str(input_path), "-ss", "00:00:01", "-vframes", "1", str(out_path)]
  proc = await asyncio.create_subprocess_exec(*args, stdout=PIPE, stderr=PIPE)
  
  # FORBIDDEN:
  # os.system(f"ffmpeg -i {untrusted_filename} ...")
  ```

### 3.2 Timeouts & Execution Bounds
- FFmpeg probe calls are bounded by a 15-second subprocess timeout.
- Keyframe extraction is capped at maximum 6 frames per video.
- Video duration is strictly capped at 300 seconds (5 minutes).

### 3.3 Temporary File Lifecycle & Cleanup
- All uploaded media and extracted frame scratches are registered in the request lifecycle.
- In both success and failure cases, `storage_service.cleanup_file(path)` and temporary directory context managers remove files immediately.
