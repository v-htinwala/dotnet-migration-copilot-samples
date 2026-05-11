---
name: video-audio-extractor
description: >
  Extracts audio tracks from video files (MP4/AVI/MKV/MOV) and generates
  timestamped text transcripts using ffmpeg and whisper. Also accepts
  user-provided transcript files (TXT/SRT/VTT) as alternative input, skipping
  extraction entirely. Use when processing application walkthrough videos that
  contain narration, voiceover, or spoken commentary to enrich downstream
  functional test generation with transcript context. Outputs audio.wav and
  transcript.json with timestamped segments. Falls back gracefully when video
  has no audio track.
license: MIT
compatibility: >
  Requires Python 3.8+, ffmpeg installed and on PATH, and openai-whisper
  (pip install openai-whisper). Works on Windows, macOS, and Linux. GPU
  recommended for faster whisper transcription but CPU fallback supported.
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Video Audio Extractor

## Purpose

Extract audio from video recordings and generate timestamped text transcripts.
This skill bridges video walkthrough recordings with text-based analysis by
producing structured transcript segments that downstream skills
(video-journey-analyzer, functional-scenario-merger) can correlate with visual
frame data.

## When to Use This Skill

- Extract narration/voiceover from application demo videos
- Generate timestamped transcripts for enriching video-sourced test scenarios
- Accept user-provided transcripts (SRT/VTT/TXT) when automatic transcription
  is unnecessary or when a higher-quality transcript is already available
- Feed transcript data to video-journey-analyzer for narration-visual correlation

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `video_path` | Yes (unless `transcript_path` provided) | — | Path to video file (MP4/AVI/MKV/MOV) |
| `transcript_path` | No | — | Path to user-provided transcript (TXT/SRT/VTT). If provided, skip audio extraction and transcription |
| `output_dir` | Yes | — | Output directory for generated files |
| `whisper_model` | No | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |
| `language` | No | auto-detect | Language hint for whisper (ISO 639-1 code, e.g., `en`) |

## Outputs

| File | Format | Description |
|---|---|---|
| `audio.wav` | WAV (16kHz mono) | Extracted audio track (skipped if transcript_path provided) |
| `transcript.json` | JSON | Timestamped transcript segments |

### Transcript JSON Format

```json
{
  "source": "whisper",
  "model": "base",
  "language": "en",
  "duration_seconds": 245,
  "segments": [
    {
      "id": 1,
      "start": "00:05",
      "end": "00:12",
      "start_seconds": 5.0,
      "end_seconds": 12.0,
      "text": "Now I'm going to show you how to create a new vehicle"
    },
    {
      "id": 2,
      "start": "00:12",
      "end": "00:18",
      "start_seconds": 12.0,
      "end_seconds": 18.0,
      "text": "First we need to fill in the vehicle name and select the type"
    }
  ]
}
```

When a user-provided transcript is used:

```json
{
  "source": "user-provided",
  "model": null,
  "language": null,
  "duration_seconds": null,
  "segments": [
    {
      "id": 1,
      "start": "00:05",
      "end": "00:12",
      "start_seconds": 5.0,
      "end_seconds": 12.0,
      "text": "Now I'm going to show you how to create a new vehicle"
    }
  ]
}
```

---

## 3-Phase Workflow

### Phase 1: Input Analysis

**Goal**: Determine the extraction path based on available inputs.

1. **Check for user-provided transcript**:
   - If `transcript_path` is provided and file exists → skip to Phase 3
     (parse the provided transcript)
   - Supported transcript formats: `.srt`, `.vtt`, `.txt`

2. **Validate video file**:
   - Verify `video_path` exists and has a supported extension
   - Supported video formats: `.mp4`, `.avi`, `.mkv`, `.mov`

3. **Probe audio track**:
   - Run `ffprobe` to check if video contains an audio stream
   - If no audio stream found:
     - Log warning: "Video has no audio track. Skipping audio extraction."
     - Create empty transcript: `{"source": "none", "segments": []}`
     - Exit gracefully — this is NOT an error

### Phase 2: Audio Extraction

**Goal**: Extract audio track from video file using ffmpeg.

1. **Extract audio**:
   ```bash
   ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 16000 -ac 1 {output_dir}/audio.wav -y
   ```
   Parameters:
   - `-vn`: No video output
   - `-acodec pcm_s16le`: 16-bit PCM WAV format
   - `-ar 16000`: 16kHz sample rate (optimal for whisper)
   - `-ac 1`: Mono channel

2. **Verify extraction**:
   - Check `audio.wav` exists and size > 0
   - If extraction fails, log error and create empty transcript

### Phase 3: Transcription

**Goal**: Generate timestamped transcript from audio or parse user-provided
transcript.

#### Path A: Whisper Transcription (from extracted audio)

1. **Load whisper model**:
   ```python
   import whisper
   model = whisper.load_model(whisper_model)  # default: "base"
   ```

2. **Transcribe**:
   ```python
   result = model.transcribe(
       audio_path,
       language=language,  # None for auto-detect
       verbose=False
   )
   ```

3. **Format segments**: Convert whisper output to transcript.json format:
   - Round timestamps to nearest second
   - Format as `MM:SS` for human-readable fields
   - Preserve float seconds for programmatic correlation

#### Path B: Parse User-Provided Transcript

1. **SRT format** (`.srt`):
   - Parse numbered blocks with timestamps: `HH:MM:SS,mmm --> HH:MM:SS,mmm`
   - Extract text lines between timestamp and next blank line

2. **VTT format** (`.vtt`):
   - Skip `WEBVTT` header
   - Parse timestamp lines: `HH:MM:SS.mmm --> HH:MM:SS.mmm`
   - Extract text lines

3. **TXT format** (`.txt`):
   - Treat entire file as a single segment with `start: "00:00"`
   - If lines contain timestamp patterns (`[MM:SS]` or `(MM:SS)`), parse them

4. **Write** `transcript.json` to `output_dir`.

---

## Script Usage

```bash
# Full extraction + transcription
python scripts/extract_audio.py \
  --video /path/to/demo.mp4 \
  --output-dir /path/to/output \
  --whisper-model base \
  --language en

# With user-provided transcript (skips extraction)
python scripts/extract_audio.py \
  --transcript /path/to/narration.srt \
  --output-dir /path/to/output

# Auto-detect language
python scripts/extract_audio.py \
  --video /path/to/demo.mp4 \
  --output-dir /path/to/output
```

---

## Constraints

1. **Audio-only extraction**: Never process or output video frames — that is
   the responsibility of video-frame-extract.
2. **Graceful degradation**: If video has no audio, produce an empty transcript
   and continue — never fail the pipeline.
3. **Model size tradeoff**: `tiny`/`base` are fast but less accurate; `medium`/
   `large` are slow but more accurate. Default to `base` for pipeline speed.
4. **File size awareness**: For videos >1 hour, warn that transcription may
   take several minutes with CPU-only inference.
5. **Encoding**: All text output in UTF-8.

## Error Handling

| Error | Behavior |
|---|---|
| Video file not found | Fail with clear error message |
| Unsupported video format | Fail with list of supported formats |
| No audio track in video | Warn, create empty transcript, exit successfully |
| ffmpeg not installed | Fail with installation instructions |
| whisper not installed | Fail with `pip install openai-whisper` instruction |
| Transcription timeout | Write partial transcript (segments processed so far) |
| User transcript parse error | Warn, attempt best-effort parse, flag low confidence |

## Related Skills

| Skill | Relationship |
|---|---|
| **video-frame-extract** | Upstream — extracts frames from the same video |
| **video-journey-analyzer** | Downstream — consumes transcript.json to correlate narration with visual frames |
| **functional-scenario-merger** | Downstream — merges video-sourced scenarios enriched with transcript data |
