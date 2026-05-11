---
name: video-functional-frame-extract
description: >
  Extracts key UI screens and application states from video recordings (MP4,
  AVI, MKV, MOV) as individual images using OpenCV scene-change detection,
  optimized for functional test case generation. Uses higher sensitivity
  defaults (threshold 0.95) to capture detailed UI state changes including
  form field interactions, validation message appearances, modal transitions,
  and inline error states that functional testing requires. Outputs numbered
  PNG/JPG files and a manifest.json with frame timestamps for downstream
  functional test scenario generation via video-functional-journey-analyzer.
  Use when extracting frames from application walkthrough videos as input to
  the functional test pipeline.
compatibility: >
  Requires Python 3.8+ and opencv-python (pip install opencv-python).
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Video Functional Frame Extraction

## Purpose

Extract visually distinct frames from application walkthrough videos for
**functional test case generation**. This skill captures detailed UI state
changes — form field interactions, validation message appearances, error states,
modal transitions, and navigation events — that the downstream
`video-functional-journey-analyzer` needs to produce technically detailed
scenario candidates.

> **Key Differentiator vs UAT**: Uses **higher sensitivity** (threshold 0.95
> by default) to capture fine-grained UI changes like inline validation errors,
> field focus states, hover states, and character counter updates. The UAT
> version uses lower sensitivity (0.70) because it only needs major screen
> transitions for business-level journey mapping.

## When to Use This Skill

- **Extract detailed UI state frames** for functional test case generation —
  captures form states, validation messages, error indicators, and field-level
  interactions
- Extract only visually distinct frames using scene-change detection — captures
  different application states while skipping redundant frames
- Prepare video frames for the `video-functional-journey-analyzer` skill which
  performs OCR and technical element extraction
- Generate frame manifest with timestamps for functional test traceability

## Prerequisites

```bash
pip install opencv-python
```

No other dependencies required.

## Quick Start

Extract key UI states with high-sensitivity scene detection (recommended for
functional test generation):

```bash
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir functional-tests/intermediate/video/frames \
  --scene-detect \
  --threshold 0.95 \
  --format jpg \
  --quality 95
```

## Usage

### Required Arguments

| Argument | Description |
|---|---|
| `--input` | Path to the input video file |
| `--output-dir` | Directory to save extracted frames |

### Optional Arguments

| Argument | Default | Description |
|---|---|---|
| `--every-n` | `1` | Extract every Nth frame (1 = all frames) |
| `--format` | `png` | Output image format: `png` (lossless) or `jpg` |
| `--quality` | `95` | JPEG quality 1-100 (higher = better OCR accuracy downstream) |
| `--prefix` | `frame` | Filename prefix for output images |
| `--scene-detect` | off | Enable scene-change detection mode |
| `--threshold` | `0.95` | Similarity threshold for scene detection. **Higher = more frames captured = more UI detail** |
| `--min-interval` | `3` | Minimum frames between captures (lower than UAT to catch rapid UI changes) |
| `--manifest` | auto | Path to output JSON manifest |

### Recommended Defaults for Functional Testing

```bash
python scripts/extract_frames.py \
  --input walkthrough.mp4 \
  --output-dir functional-tests/intermediate/video/frames \
  --scene-detect \
  --threshold 0.95 \
  --min-interval 3 \
  --format jpg \
  --quality 95
```

**Why these defaults?**
- **Threshold 0.95**: Captures fine-grained UI state changes (validation message
  appearing, field focus change, character counter update, hover states) that
  functional tests need. A 2-minute UI demo typically produces 80-150 frames
  at this sensitivity.
- **Min-interval 3**: Allows capturing rapid UI transitions (form submit →
  validation error → field highlight) that happen within 0.1-0.5 seconds.
- **Quality 95**: High quality preserves text clarity for OCR extraction
  downstream in `video-functional-journey-analyzer`.

### Tuning for Specific Scenarios

```bash
# Very detailed — captures micro-interactions (tooltips, hover, focus rings)
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir ./detailed_frames \
  --scene-detect \
  --threshold 0.98 \
  --min-interval 2

# Standard functional — captures form states, validation, hover (recommended)
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir ./standard_frames \
  --scene-detect \
  --threshold 0.95

# Light functional — captures form states and major transitions
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir ./light_frames \
  --scene-detect \
  --threshold 0.92
```

## Output

- Frames are saved as `{prefix}_{number}.{format}` with zero-padded 6-digit
  numbering: `frame_000001.jpg`, `frame_000002.jpg`, ...
- **manifest.json** is generated with frame metadata:

```json
{
  "video_path": "demo.mp4",
  "total_frames_processed": 3600,
  "frames_saved": 95,
  "video_resolution": "1920x1080",
  "fps": 30,
  "duration_seconds": 120,
  "threshold": 0.95,
  "frames": [
    {
      "filename": "frame_000001.jpg",
      "frame_number": 1,
      "timestamp_seconds": 0.033,
      "timestamp_formatted": "00:00",
      "similarity_to_previous": null
    },
    {
      "filename": "frame_000002.jpg",
      "frame_number": 45,
      "timestamp_seconds": 1.5,
      "timestamp_formatted": "00:01",
      "similarity_to_previous": 0.78
    }
  ]
}
```

## Edge Cases and Troubleshooting

- **Video file not found**: Script exits with clear error message and exit code 1.
- **Corrupted or unreadable video**: Script reports the error and exits gracefully.
- **Too many frames**: If >200 frames extracted, consider lowering threshold
  to 0.92-0.93 to reduce noise while keeping important UI states.
- **Too few frames** (<20 for a 2+ minute demo): Raise threshold to 0.97-0.98
  or use `--every-n 15` as a fallback.
- **Output directory doesn't exist**: Script creates it automatically.
- **Codec issues**: Install `opencv-python-headless` for server environments.

## Constraints

1. **Scene detection recommended**: For functional testing, always use
   `--scene-detect` mode rather than every-N extraction. Scene detection
   captures meaningful UI state changes; every-N captures arbitrary frames.
2. **High quality for OCR**: Use `--quality 95` (jpg) or `--format png` to
   preserve text clarity for downstream OCR extraction.
3. **Manifest required**: Always generate `manifest.json` — it is required
   input for `video-functional-journey-analyzer`.
4. **Output to pipeline directory**: Default output should go to
   `functional-tests/intermediate/video/frames/` to integrate with the
   functional test orchestrator's directory structure.

## Related Skills

| Skill | Relationship |
|---|---|
| **video-functional-journey-analyzer** | Downstream — consumes frames/ and manifest.json for functional scenario extraction |
| **video-audio-extractor** | Parallel — extracts audio from the same video for transcript |
| **functional-test-orchestrator** | Orchestrator — invokes this skill as Phase 1a |

## Reference

See [references/REFERENCE.md](references/REFERENCE.md) for detailed technical
documentation including frame naming conventions, performance tips, and OpenCV
backend troubleshooting.
