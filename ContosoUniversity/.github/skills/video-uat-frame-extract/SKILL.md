---
name: video-uat-frame-extract
description: >
  Extracts key UI screens and major application states from video recordings
  (MP4, AVI, MKV, MOV) as individual images using OpenCV scene-change
  detection, optimized for UAT test case generation. Uses lower sensitivity
  defaults (threshold 0.70) to capture only major screen transitions —
  page navigations, form submissions, confirmation dialogs, and workflow
  completions — that represent distinct steps in a user's business journey.
  Skips minor UI changes (field focus, character counters, hover states)
  that are irrelevant to UAT. Outputs numbered PNG/JPG files and a
  manifest.json with frame timestamps for downstream UAT scenario generation
  via video-uat-journey-analyzer. Use when extracting frames from application
  walkthrough videos as input to the UAT test pipeline.
compatibility: >
  Requires Python 3.8+ and opencv-python (pip install opencv-python).
metadata:
  author: uat-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Video UAT Frame Extraction

## Purpose

Extract visually distinct frames from application walkthrough videos for
**UAT test case generation**. This skill captures only major screen transitions
— page navigations, full form submissions, confirmation screens, error pages,
and workflow completions — that represent meaningful steps in the user's
business journey.

> **Key Differentiator vs Functional**: Uses **lower sensitivity** (threshold
> 0.70 by default) to capture only major screen changes. UAT testing cares
> about "what screens does the user see?" not "what specific field states
> changed?". This produces 30-50 frames from a typical 2-minute demo,
> focusing on complete page/state transitions relevant to acceptance criteria.

## When to Use This Skill

- **Extract major screen transitions** for UAT journey mapping — captures
  page navigations, form completions, and outcome screens
- Skip minor UI changes (field focus, validation indicators, hover states)
  that are irrelevant to business-level acceptance testing
- Prepare video frames for the `video-uat-journey-analyzer` skill which
  produces business-language scenario candidates
- Generate frame manifest with timestamps for UAT test traceability

## Prerequisites

```bash
pip install opencv-python
```

No other dependencies required.

## Quick Start

Extract major screen transitions for UAT scenario generation:

```bash
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir uat-output/phase-1-video/frames \
  --scene-detect \
  --threshold 0.70 \
  --format jpg \
  --quality 90
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
| `--quality` | `90` | JPEG quality 1-100 (90 is sufficient for visual analysis) |
| `--prefix` | `frame` | Filename prefix for output images |
| `--scene-detect` | off | Enable scene-change detection mode |
| `--threshold` | `0.70` | Similarity threshold for scene detection. **Lower = fewer frames = only major transitions** |
| `--min-interval` | `5` | Minimum frames between captures (higher to skip animation bursts) |
| `--manifest` | auto | Path to output JSON manifest |

### Recommended Defaults for UAT

```bash
python scripts/extract_frames.py \
  --input walkthrough.mp4 \
  --output-dir uat-output/phase-1-video/frames \
  --scene-detect \
  --threshold 0.70 \
  --min-interval 5 \
  --format jpg \
  --quality 90
```

**Why these defaults?**
- **Threshold 0.70**: Captures only major screen changes (new page, form
  submitted, error page). Skips minor changes (field focus, hover tooltip).
  A 2-minute UI demo typically produces 30-50 frames at this sensitivity.
- **Min-interval 5**: Skips animation bursts and loading transitions that
  don't represent meaningful user journey steps.
- **Quality 90**: Sufficient for visual analysis. UAT doesn't need OCR-level
  text clarity — business language descriptions are preferred.

### Tuning for Specific Scenarios

```bash
# Minimal — captures only full page transitions (for high-level UAT)
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir ./major_screens \
  --scene-detect \
  --threshold 0.60

# Standard UAT — captures page transitions and form state changes
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir ./uat_frames \
  --scene-detect \
  --threshold 0.70

# Detailed UAT — captures more state changes for complex workflows
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir ./detailed_uat \
  --scene-detect \
  --threshold 0.80
```

## Output

- Frames are saved as `{prefix}_{number}.{format}` with zero-padded 6-digit
  numbering: `frame_000001.jpg`, `frame_000002.jpg`, ...
- **manifest.json** is generated with frame metadata:

```json
{
  "video_path": "demo.mp4",
  "total_frames_processed": 3600,
  "frames_saved": 38,
  "video_resolution": "1920x1080",
  "fps": 30,
  "duration_seconds": 120,
  "threshold": 0.70,
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
      "frame_number": 90,
      "timestamp_seconds": 3.0,
      "timestamp_formatted": "00:03",
      "similarity_to_previous": 0.62
    }
  ]
}
```

## Edge Cases and Troubleshooting

- **Video file not found**: Script exits with clear error message and exit code 1.
- **Corrupted or unreadable video**: Script reports the error and exits gracefully.
- **Too many frames** (>60 for a 2-minute demo): Lower threshold to 0.60-0.65
  to capture only the most significant transitions.
- **Too few frames** (<15 for a 2+ minute demo): Raise threshold to 0.75-0.80.
- **Output directory doesn't exist**: Script creates it automatically.
- **Codec issues**: Install `opencv-python-headless` for server environments.

## Constraints

1. **Scene detection recommended**: For UAT, always use `--scene-detect` mode.
   Scene detection captures meaningful page transitions; every-N captures
   arbitrary frames including mid-animation states.
2. **Sufficient quality**: Use `--quality 90` (jpg) — UAT doesn't need
   OCR-level text clarity since the downstream analyzer uses visual inference
   in business language.
3. **Manifest required**: Always generate `manifest.json` — it is required
   input for `video-uat-journey-analyzer`.
4. **Output to pipeline directory**: Default output should go to
   `uat-output/phase-1-video/frames/` to integrate with the UAT orchestrator's
   directory structure.

## Related Skills

| Skill | Relationship |
|---|---|
| **video-uat-journey-analyzer** | Downstream — consumes frames/ and manifest.json for UAT scenario extraction |
| **video-audio-extractor** | Parallel — extracts audio from the same video for transcript |
| **uat-test-orchestrator** | Orchestrator — invokes this skill in the video pipeline phase |

## Reference

See [references/REFERENCE.md](references/REFERENCE.md) for detailed technical
documentation including frame naming conventions, performance tips, and OpenCV
backend troubleshooting.
