---
name: video-regression-frame-extract
description: >
  Extracts UI state transitions from video recordings (MP4, AVI, MKV, MOV)
  as individual images using OpenCV scene-change detection, optimized for
  regression test case generation. Uses moderate sensitivity defaults
  (threshold 0.85) to capture all meaningful UI state changes including —
  page navigations, form validations, error states, loading indicators,
  component renders, modal dialogs, and hover/focus transitions — that
  represent testable interaction points for regression coverage.
  Captures more technical state changes than UAT extraction. Outputs
  numbered PNG/JPG files and a manifest.json with frame timestamps for
  downstream regression scenario generation via video-regression-journey-analyzer.
  Use when extracting frames from application walkthrough videos as input
  to the regression test pipeline.
compatibility: >
  Requires Python 3.8+ and opencv-python (pip install opencv-python).
metadata:
  author: regression-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Video Regression Frame Extraction

## Purpose

Extract visually distinct frames from application walkthrough videos for
**regression test case generation**. This skill captures all meaningful UI
state changes — page navigations, form validations, error states, loading
indicators, component renders, modal dialogs, and interaction feedback — that
represent testable points for regression coverage.

> **Key Differentiator vs UAT**: Uses **moderate sensitivity** (threshold 0.85
> by default) to capture a broader range of UI state changes. Regression testing
> cares about "did the component behavior change?" and needs to capture
> fine-grained state transitions including validation feedback, loading states,
> and conditional UI rendering. UAT captures business-level screens;
> regression captures technical interaction states.

## When to Use This Skill

- **Extract all UI state transitions** for regression test mapping — captures
  page changes, validation states, error feedback, loading indicators, and
  component interaction responses
- Capture more granular state changes than UAT extraction to ensure regression
  coverage of component behavior, conditional rendering, and edge cases
- Prepare video frames for the `video-regression-journey-analyzer` skill which
  produces technical regression scenario candidates
- Generate frame manifest with timestamps for regression test traceability

## Prerequisites

```bash
pip install opencv-python
```

No other dependencies required.

## Quick Start

Extract UI state transitions for regression scenario generation:

```bash
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir regression-output/phase-1-video/frames \
  --scene-detect \
  --threshold 0.85 \
  --format png \
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
| `--format` | `png` | Output image format: `png` (lossless for precise pixel comparison) or `jpg` |
| `--quality` | `95` | JPEG quality 1-100 (95 for regression to preserve validation text clarity) |
| `--prefix` | `frame` | Filename prefix for output images |
| `--scene-detect` | off | Enable scene-change detection mode |
| `--threshold` | `0.85` | Similarity threshold for scene detection. **Lower = fewer frames, Higher = more frames** |
| `--min-interval` | `5` | Minimum frames between captures (higher to skip animation bursts) |
| `--manifest` | auto | Path to output JSON manifest |

### Recommended Defaults for Regression

```bash
python scripts/extract_frames.py \
  --input walkthrough.mp4 \
  --output-dir regression-output/phase-1-video/frames \
  --scene-detect \
  --threshold 0.85 \
  --min-interval 5 \
  --format png \
  --quality 95
```

**Why these defaults?**
- **Threshold 0.85**: Captures all distinct screen transitions including
  validation states, error messages, and component state changes. Produces
  30–80 frames for a typical 2-minute UI demo — enough for comprehensive
  regression coverage without excessive noise.
- **Min-interval 5**: Skips animation frames and CSS transitions that don't
  represent distinct testable states.
- **Format PNG / Quality 95**: Lossless PNG preserves text clarity for OCR
  extraction of validation messages, field labels, and error text that
  regression tests need to verify.

### Tuning for Specific Scenarios

```bash
# Broad regression — captures major page transitions only
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir ./major_states \
  --scene-detect \
  --threshold 0.70

# Standard regression — captures page transitions + component state changes
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir ./regression_frames \
  --scene-detect \
  --threshold 0.85

# Detailed regression — captures fine-grained UI changes (hover, focus, validation)
python scripts/extract_frames.py \
  --input demo.mp4 \
  --output-dir ./detailed_regression \
  --scene-detect \
  --threshold 0.95

# Component-level regression — maximum sensitivity for single-component demos
python scripts/extract_frames.py \
  --input component-demo.mp4 \
  --output-dir ./component_frames \
  --scene-detect \
  --threshold 0.97 \
  --min-interval 3
```

## Output

- Frames are saved as `{prefix}_{number}.{format}` with zero-padded 6-digit
  numbering: `frame_000001.png`, `frame_000002.png`, ...
- **manifest.json** is generated with frame metadata:

```json
{
  "video_path": "demo.mp4",
  "total_frames_processed": 3600,
  "frames_saved": 52,
  "video_resolution": "1920x1080",
  "fps": 30,
  "duration_seconds": 120,
  "threshold": 0.85,
  "frames": [
    {
      "filename": "frame_000001.png",
      "frame_number": 1,
      "timestamp_seconds": 0.033,
      "timestamp_formatted": "00:00",
      "similarity_to_previous": null
    },
    {
      "filename": "frame_000002.png",
      "frame_number": 45,
      "timestamp_seconds": 1.5,
      "timestamp_formatted": "00:01",
      "similarity_to_previous": 0.72
    }
  ]
}
```

## Edge Cases and Troubleshooting

- **Video file not found**: Script exits with clear error message and exit code 1.
- **Corrupted or unreadable video**: Script reports the error and exits gracefully.
- **Too many frames** (>100 for a 2-minute demo): Lower threshold to 0.70
  to capture only major state transitions.
- **Too few frames** (<20 for a 2+ minute demo): Raise threshold to 0.90-0.95.
- **Output directory doesn't exist**: Script creates it automatically.
- **Codec issues**: Install `opencv-python-headless` for server environments.

## Constraints

1. **Scene detection recommended**: For regression, always use `--scene-detect`
   mode. Scene detection captures testable state transitions; every-N captures
   arbitrary frames including mid-animation states.
2. **High quality preferred**: Use PNG or `--quality 95` (jpg) — regression
   needs OCR-readable text for validation messages, field labels, and error
   codes that tests must assert against.
3. **Manifest required**: Always generate `manifest.json` — it is required
   input for `video-regression-journey-analyzer`.
4. **Output to pipeline directory**: Default output should go to
   `regression-output/phase-1-video/frames/` to integrate with the regression
   orchestrator's directory structure.

## Related Skills

| Skill | Relationship |
|---|---|
| **video-regression-journey-analyzer** | Downstream — consumes frames/ and manifest.json for regression scenario extraction |
| **video-audio-extractor** | Parallel — extracts audio from the same video for transcript |
| **regression-orchestrator** | Orchestrator — can invoke this skill in the video pipeline phase |

## Reference

See [references/REFERENCE.md](references/REFERENCE.md) for detailed technical
documentation including frame naming conventions, performance tips, and OpenCV
backend troubleshooting.
