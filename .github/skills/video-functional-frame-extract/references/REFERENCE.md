# Video Frame Extraction — Technical Reference

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
| `--threshold`  | float  | No       | `0.95`  | Similarity threshold for scene detection (0.0–1.0)    |
| `--min-interval` | int  | No       | `5`     | Minimum frames between scene-detect captures          |
| `--manifest`   | string | No       | auto    | Path to output JSON manifest file                     |

## Frame naming convention

Frames are saved with zero-padded numbering starting from 1:

```
{prefix}_{number}.{format}
```

- The number represents the **saved frame sequence number** (not the source frame index).
- Zero-padding is at least 6 digits (e.g., `frame_000001.png`), and will extend further if the expected frame count exceeds 999,999.
- This ensures correct lexicographic sorting by all file managers and tools.

### Example output for a 150-frame video (`--every-n 1`)

```
frame_000001.png
frame_000002.png
...
frame_000150.png
```

### Example output for a 3000-frame video (`--every-n 30`)

```
frame_000001.png
frame_000002.png
...
frame_000100.png
```

## Calculating useful values

### Frames per second → `--every-n` mapping

To extract approximately one frame per second:

```
--every-n = round(FPS)
```

For example, a 29.97 FPS video → `--every-n 30`.

To extract one frame every K seconds:

```
--every-n = round(FPS * K)
```

### Estimating total saved frames

```
saved_frames = ceil(total_frames / every_n)
```

### Estimating disk space

| Format | Approximate size per frame (1920×1080) |
| ------ | -------------------------------------- |
| PNG    | 2–5 MB                                |
| JPG 95 | 200–500 KB                            |
| JPG 85 | 100–250 KB                            |
| JPG 50 | 40–100 KB                             |

For a 30 FPS, 10-minute video (18,000 frames):

- **All frames as PNG**: ~36–90 GB
- **All frames as JPG 85**: ~1.8–4.5 GB
- **Every 30th frame as PNG**: ~1.2–3 GB (600 frames)
- **Every 30th frame as JPG 85**: ~60–150 MB (600 frames)

## Performance tips

### Large videos

For videos longer than a few minutes, extracting every frame produces a massive number of files. Recommendations:

1. **Use `--every-n`** to skip frames. For most use cases (thumbnails, review), one frame per second (`--every-n <fps>`) is sufficient.
2. **Use JPG format** with `--quality 85` for a good balance of quality and file size (5–10× smaller than PNG).
3. **Ensure sufficient disk space** before starting extraction. See the disk space estimates above.

### Processing speed

- The script processes frames sequentially using `cv2.VideoCapture.read()`.
- Typical throughput: 100–500 frames/sec for reading, bottlenecked by disk I/O for writing.
- PNG encoding is slower than JPG encoding; use JPG for faster extraction.
- SSD storage significantly outperforms HDD for write-heavy frame extraction.

## Supported video formats

OpenCV uses FFmpeg (or platform-specific backends) for video decoding. Commonly supported formats:

| Format    | Extension(s)         | Notes                               |
| --------- | -------------------- | ----------------------------------- |
| MP4       | `.mp4`, `.m4v`       | H.264/H.265 codecs                  |
| AVI       | `.avi`               | Various codecs (MJPEG, DivX, etc.)  |
| MKV       | `.mkv`               | Matroska container, many codecs     |
| MOV       | `.mov`               | QuickTime, common from Apple devices|
| WebM      | `.webm`              | VP8/VP9 codecs                      |
| FLV       | `.flv`               | Flash Video                         |
| WMV       | `.wmv`               | Windows Media Video                 |

## OpenCV backend troubleshooting

### "Cannot open video file" error

1. **Check the file path** — ensure it exists and is readable.
2. **Check codec support** — run `python -c "import cv2; print(cv2.getBuildInformation())"` and look for the "Video I/O" section. Ensure FFmpeg is listed.
3. **Reinstall OpenCV with FFmpeg support**:
   ```bash
   pip uninstall opencv-python opencv-python-headless
   pip install opencv-python
   ```
4. **On Linux servers**, use `opencv-python-headless` to avoid GUI dependency issues:
   ```bash
   pip install opencv-python-headless
   ```

### Frames appear corrupted or green

This usually indicates a codec issue:

- Try converting the video to H.264 MP4 first: `ffmpeg -i input.mkv -c:v libx264 output.mp4`
- Ensure your OpenCV version is up to date: `pip install --upgrade opencv-python`

### Script hangs or is extremely slow

- Some video files have incorrect metadata (e.g., reported frame count doesn't match actual content). The script reads until `cap.read()` returns `False`, so it will still complete.
- Hardware-accelerated decoding is not used by default in OpenCV's Python bindings. For very large videos, consider using FFmpeg directly for extraction.

## Exit codes

| Code | Meaning                                        |
| ---- | ---------------------------------------------- |
| `0`  | Success — frames extracted and saved           |
| `1`  | Error — file not found, invalid args, or no frames saved |

## Scene-change detection

### How it works

When `--scene-detect` is enabled, the script compares each candidate frame to the previously saved frame using normalised mean absolute pixel difference:

1. Both frames are converted to grayscale
2. Both are resized to 256×256 for fast comparison
3. `cv2.absdiff` computes per-pixel absolute difference
4. The mean difference is normalised to a 0.0–1.0 similarity score
5. If similarity < `--threshold` **and** at least `--min-interval` frames have elapsed, the frame is saved
6. The first and last frames are always saved

No additional dependencies beyond OpenCV and numpy are required.

### Threshold tuning guide

| Threshold | Behaviour | Typical frame count (2-min UI demo) | Best for |
| --------- | --------- | ----------------------------------- | -------- |
| `0.98`    | Very sensitive — captures micro-interactions (tooltips, hover states) | 120–200 | Micro-interaction capture |
| `0.95`    | **Default** — captures fine-grained UI state changes and interactions | 80–150 | Functional testing |
| `0.85`    | Moderate — captures distinct screen transitions and major interactions | 30–80 | General test-case generation |
| `0.70`    | Aggressive — only major page/view changes | 10–30 | High-level UAT scenarios |
| `0.50`    | Extreme — only drastically different screens | 5–15 | Executive summary/storyboard |

### Combining with `--every-n`

When both `--scene-detect` and `--every-n` are used, `--every-n` acts as a **pre-filter**: only every Nth frame is considered as a candidate for scene comparison. This speeds up processing for very long videos.

```bash
# Process only every 5th frame for scene comparison (5× faster)
python extract_frames.py --input long_video.mp4 --output-dir ./key --scene-detect --every-n 5
```

### Manifest JSON format

When scene detection is enabled (or `--manifest` is explicitly set), a `manifest.json` is written:

```json
{
  "video": {
    "path": "/absolute/path/to/video.mp4",
    "fps": 30.0,
    "resolution": "1920x1080",
    "duration_sec": 120.5,
    "total_frames": 3615,
    "codec": "avc1"
  },
  "extraction": {
    "mode": "scene-detect",
    "every_n": 1,
    "threshold": 0.95,
    "min_interval": 5,
    "format": "jpg",
    "quality": 90,
    "frames_saved": 42,
    "frames_read": 3615
  },
  "frames": [
    {
      "filename": "frame_000001.jpg",
      "frame_index": 0,
      "timestamp_sec": 0.0,
      "timestamp_fmt": "00:00:00.000",
      "similarity_to_previous": 0.0
    },
    {
      "filename": "frame_000002.jpg",
      "frame_index": 87,
      "timestamp_sec": 2.9,
      "timestamp_fmt": "00:00:02.900",
      "similarity_to_previous": 0.7234
    }
  ]
}
```

This manifest can be fed directly into test-case generation pipelines, LLM prompts, or visual review tools.

## Programmatic usage

The `extract_frames` function can be imported and called directly from Python:

```python
from extract_frames import extract_frames

result = extract_frames(
    input_path="video.mp4",
    output_dir="./frames",
    every_n=30,
    fmt="jpg",
    quality=85,
    prefix="frame",
)

# Scene-detect mode:
result = extract_frames(
    input_path="demo.mp4",
    output_dir="./key_frames",
    scene_detect=True,
    threshold=0.95,
    fmt="jpg",
    quality=90,
)

print(f"Saved {result['frames_saved']} frames to {result['output_dir']}")
print(f"Video resolution: {result['video_info']['width']}x{result['video_info']['height']}")
```

The returned dict contains:

```python
{
    "frames_read": int,       # Total frames read from video
    "frames_saved": int,      # Number of frames saved to disk
    "output_dir": str,        # Absolute path to output directory
    "elapsed_sec": float,     # Time taken in seconds
    "manifest_path": str,     # Absolute path to manifest.json (or None)
    "video_info": {
        "total_frames": int,
        "fps": float,
        "width": int,
        "height": int,
        "codec": str,
        "duration_sec": float,
    },
}
```
