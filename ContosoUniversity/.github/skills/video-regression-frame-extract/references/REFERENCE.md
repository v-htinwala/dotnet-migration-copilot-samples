# Video Frame Extraction (Regression) — Technical Reference

## CLI argument reference

```
python extract_frames.py --input <path> --output-dir <path> [options]
```

| Argument       | Type   | Required | Default | Description                                           |
| -------------- | ------ | -------- | ------- | ----------------------------------------------------- |
| `--input`      | string | Yes      | —       | Path to the input video file                          |
| `--output-dir` | string | Yes      | —       | Directory where extracted frames will be saved        |
| `--every-n`    | int    | No       | `1`     | Extract every Nth frame (1 = every frame)             |
| `--format`     | string | No       | `png`   | Image format: `png` (lossless) or `jpg` (lossy)      |
| `--quality`    | int    | No       | `95`    | JPEG quality 1–100 (ignored for PNG)                  |
| `--prefix`     | string | No       | `frame` | Filename prefix for saved images                      |
| `--scene-detect` | flag | No       | off     | Enable scene-change detection mode                    |
| `--threshold`  | float  | No       | `0.85`  | Similarity threshold for scene detection (0.0–1.0)    |
| `--min-interval` | int  | No       | `5`     | Minimum frames between scene-detect captures          |
| `--manifest`   | string | No       | auto    | Path to output JSON manifest file                     |

## Frame naming convention

Frames are saved with zero-padded numbering starting from 1:

```
{prefix}_{number}.{format}
```

- The number represents the **saved frame sequence number** (not the source frame index).
- Zero-padding is at least 6 digits (e.g., `frame_000001.png`).

## Regression vs UAT threshold tuning guide

| Threshold | Behaviour | Typical frame count (2-min UI demo) | Best for |
| --------- | --------- | ----------------------------------- | -------- |
| `0.97`    | Maximum — captures micro UI changes (focus rings, tooltips) | 100–200 | Component-level regression |
| `0.95`    | Very sensitive — captures small UI changes (hover, validation feedback) | 80–150 | Detailed regression testing |
| `0.85`    | **Default for regression** — captures distinct state transitions | 30–80 | Standard regression coverage |
| `0.70`    | Broad — only major page/view changes | 10–30 | High-level regression smoke tests |
| `0.50`    | Extreme — only drastically different screens | 5–15 | Visual diff baseline only |

### Why 0.85 for regression (vs 0.95 for UAT)?

- **Regression** needs to detect component state changes (validation errors appearing,
  loading spinners, conditional rendering) but not every pixel change
- **UAT** needs finer sensitivity (0.95) because it maps screen-by-screen user
  journeys where even subtle page transitions matter
- Regression at 0.85 produces 30–80 frames which is optimal for mapping to
  testable component interactions without noise from animations

## Supported video formats

| Format    | Extension(s)         | Notes                               |
| --------- | -------------------- | ----------------------------------- |
| MP4       | `.mp4`, `.m4v`       | H.264/H.265 codecs                  |
| AVI       | `.avi`               | Various codecs (MJPEG, DivX, etc.)  |
| MKV       | `.mkv`               | Matroska container, many codecs     |
| MOV       | `.mov`               | QuickTime, common from Apple devices|
| WebM      | `.webm`              | VP8/VP9 codecs                      |

## Performance tips

- Use `--every-n` to skip frames for videos longer than a few minutes
- PNG encoding is slower than JPG but preserves text clarity for OCR
- SSD storage significantly outperforms HDD for write-heavy extraction

## Exit codes

| Code | Meaning                                        |
| ---- | ---------------------------------------------- |
| `0`  | Success — frames extracted and saved           |
| `1`  | Error — file not found, invalid args, or no frames saved |

## Manifest JSON format

```json
{
  "video": {
    "path": "/absolute/path/to/video.mp4",
    "fps": 30.0,
    "resolution": "1920x1080",
    "duration_sec": 120.0,
    "total_frames": 3600,
    "codec": "avc1"
  },
  "extraction": {
    "mode": "scene-detect",
    "every_n": 1,
    "threshold": 0.85,
    "min_interval": 5,
    "format": "png",
    "quality": null,
    "frames_saved": 52,
    "frames_read": 3600
  },
  "frames": [
    {
      "filename": "frame_000001.png",
      "frame_index": 0,
      "timestamp_sec": 0.0,
      "timestamp_fmt": "00:00:00.000",
      "similarity_to_previous": 0.0
    }
  ]
}
```
