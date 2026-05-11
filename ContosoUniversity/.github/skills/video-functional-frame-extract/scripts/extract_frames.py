#!/usr/bin/env python3
"""
Video Frame Extractor
=====================
Extracts frames (screenshots) from a video file and saves them as individual images.

Usage:
    python extract_frames.py --input video.mp4 --output-dir ./frames
    python extract_frames.py --input video.mp4 --output-dir ./frames --every-n 30
    python extract_frames.py --input video.mp4 --output-dir ./frames --format jpg --quality 85
    python extract_frames.py --input video.mp4 --output-dir ./frames --scene-detect
    python extract_frames.py --input video.mp4 --output-dir ./frames --scene-detect --threshold 0.90

Requirements:
    pip install opencv-python
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import cv2
except ImportError:
    print(
        "Error: opencv-python is not installed.\n"
        "Install it with: pip install opencv-python",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract frames from a video file as individual images using OpenCV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --input video.mp4 --output-dir ./frames\n"
            "  %(prog)s --input video.mp4 --output-dir ./frames --every-n 30\n"
            "  %(prog)s --input video.mp4 --output-dir ./frames --format jpg --quality 85\n"
        ),
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input video file.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to save extracted frame images.",
    )
    parser.add_argument(
        "--every-n",
        type=int,
        default=1,
        help="Extract every Nth frame. Default: 1 (all frames).",
    )
    parser.add_argument(
        "--format",
        choices=["png", "jpg"],
        default="png",
        help="Output image format. Default: png.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=95,
        help="JPEG quality (1-100). Only used when --format is jpg. Default: 95.",
    )
    parser.add_argument(
        "--prefix",
        default="frame",
        help="Filename prefix for output images. Default: frame.",
    )
    parser.add_argument(
        "--scene-detect",
        action="store_true",
        default=False,
        help="Enable scene-change detection mode. Only saves frames that differ "
             "significantly from the previous saved frame.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="Similarity threshold for scene detection (0.0-1.0). Frames with "
             "similarity below this value vs. the last saved frame are saved. "
             "Lower = fewer frames, higher = more frames. Default: 0.95.",
    )
    parser.add_argument(
        "--min-interval",
        type=int,
        default=5,
        help="Minimum number of frames between scene-detect captures to skip "
             "burst changes during animations. Default: 5.",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to output JSON manifest file. Defaults to "
             "{output-dir}/manifest.json when --scene-detect is enabled.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate parsed arguments and exit on errors."""
    if not os.path.isfile(args.input):
        print(f"Error: Input video file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.every_n < 1:
        print("Error: --every-n must be >= 1.", file=sys.stderr)
        sys.exit(1)

    if args.quality < 1 or args.quality > 100:
        print("Error: --quality must be between 1 and 100.", file=sys.stderr)
        sys.exit(1)

    if args.threshold < 0.0 or args.threshold > 1.0:
        print("Error: --threshold must be between 0.0 and 1.0.", file=sys.stderr)
        sys.exit(1)

    if args.min_interval < 1:
        print("Error: --min-interval must be >= 1.", file=sys.stderr)
        sys.exit(1)


def get_video_info(cap: cv2.VideoCapture) -> dict:
    """Extract video metadata from a VideoCapture object."""
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    codec_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec = "".join(chr((codec_int >> (8 * i)) & 0xFF) for i in range(4))
    duration_sec = total_frames / fps if fps > 0 else 0.0

    return {
        "total_frames": total_frames,
        "fps": fps,
        "width": width,
        "height": height,
        "codec": codec,
        "duration_sec": duration_sec,
    }


def format_duration(seconds: float) -> str:
    """Format seconds into HH:MM:SS.mmm string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


import numpy as np


def compute_similarity(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    """Compute similarity between two frames using normalised mean absolute difference.

    Converts both frames to grayscale, resizes to a small canonical size for
    speed, then computes the mean absolute pixel difference normalised to
    [0, 1].  Returns 1.0 for identical frames and 0.0 for maximally different.

    This is intentionally simple (no extra dependencies beyond OpenCV/numpy)
    and works very well for UI screenshot comparison where scene changes
    produce large, sharp pixel differences.
    """
    _COMPARE_SIZE = (256, 256)

    gray_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)

    small_a = cv2.resize(gray_a, _COMPARE_SIZE, interpolation=cv2.INTER_AREA)
    small_b = cv2.resize(gray_b, _COMPARE_SIZE, interpolation=cv2.INTER_AREA)

    diff = cv2.absdiff(small_a, small_b)
    mean_diff = float(np.mean(diff)) / 255.0  # normalise to 0-1
    similarity = 1.0 - mean_diff
    return similarity


def build_encode_params(fmt: str, quality: int) -> list:
    """Build OpenCV imwrite params based on format and quality."""
    if fmt == "jpg":
        return [cv2.IMWRITE_JPEG_QUALITY, quality]
    elif fmt == "png":
        # PNG compression level 3 (0=no compression, 9=max compression)
        # Level 3 is a good speed/size trade-off
        return [cv2.IMWRITE_PNG_COMPRESSION, 3]
    return []


def extract_frames(
    input_path: str,
    output_dir: str,
    every_n: int = 1,
    fmt: str = "png",
    quality: int = 95,
    prefix: str = "frame",
    scene_detect: bool = False,
    threshold: float = 0.95,
    min_interval: int = 5,
    manifest_path: str | None = None,
) -> dict:
    """
    Extract frames from a video file and save them as images.

    Args:
        input_path: Path to the input video file.
        output_dir: Directory to save extracted frames.
        every_n: Extract every Nth frame (1 = all frames).
        fmt: Output image format ('png' or 'jpg').
        quality: JPEG quality (1-100), only used for jpg.
        prefix: Filename prefix for output images.
        scene_detect: Enable scene-change detection mode.
        threshold: Similarity threshold for scene detection (0.0-1.0).
        min_interval: Minimum frames between scene-detect captures.
        manifest_path: Path for JSON manifest (default: {output_dir}/manifest.json).

    Returns:
        A dict with extraction results/statistics.
    """
    # Open video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video file: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Get video info
    info = get_video_info(cap)
    print("=" * 60)
    print("Video Frame Extractor")
    print("=" * 60)
    print(f"  Input       : {input_path}")
    print(f"  Resolution  : {info['width']}x{info['height']}")
    print(f"  FPS         : {info['fps']:.2f}")
    print(f"  Total frames: {info['total_frames']}")
    print(f"  Duration    : {format_duration(info['duration_sec'])}")
    print(f"  Codec       : {info['codec']}")
    print(f"  Output dir  : {output_dir}")
    print(f"  Format      : {fmt}")
    if scene_detect:
        print(f"  Mode        : scene-detect")
        print(f"  Threshold   : {threshold}")
        print(f"  Min interval: {min_interval} frames")
    else:
        print(f"  Every N     : {every_n}")
    if fmt == "jpg":
        print(f"  JPEG quality: {quality}")
    print("=" * 60)

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Prepare encoding params
    encode_params = build_encode_params(fmt, quality)

    # Calculate zero-padding width based on expected number of saved frames
    expected_saved = (info["total_frames"] + every_n - 1) // every_n
    pad_width = max(6, len(str(expected_saved)))

    # Extract frames
    frame_index = 0
    saved_count = 0
    start_time = time.time()
    last_progress_time = start_time

    # Scene-detect state
    last_saved_frame = None
    last_saved_index = -min_interval  # allow first frame to be saved immediately
    manifest_entries = []  # list of dicts for manifest.json
    last_frame = None  # keep reference to the very last frame for final save

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        last_frame = frame
        should_save = False
        sim_score = None

        if scene_detect:
            # Pre-filter with every_n: only consider frames at every_n intervals
            if frame_index % every_n == 0:
                if last_saved_frame is None:
                    # Always save the first candidate frame
                    should_save = True
                    sim_score = 0.0
                else:
                    sim_score = compute_similarity(last_saved_frame, frame)
                    frames_since_last = frame_index - last_saved_index
                    if sim_score < threshold and frames_since_last >= min_interval:
                        should_save = True
        else:
            # Original mode: save every Nth frame
            if frame_index % every_n == 0:
                should_save = True

        if should_save:
            saved_count += 1
            filename = f"{prefix}_{saved_count:0{pad_width}d}.{fmt}"
            filepath = os.path.join(output_dir, filename)

            success = cv2.imwrite(filepath, frame, encode_params)
            if not success:
                print(
                    f"Warning: Failed to write frame {frame_index} to {filepath}",
                    file=sys.stderr,
                )
            else:
                if scene_detect:
                    timestamp_sec = frame_index / info["fps"] if info["fps"] > 0 else 0.0
                    manifest_entries.append({
                        "filename": filename,
                        "frame_index": frame_index,
                        "timestamp_sec": round(timestamp_sec, 3),
                        "timestamp_fmt": format_duration(timestamp_sec),
                        "similarity_to_previous": round(sim_score, 4) if sim_score is not None else None,
                    })

            last_saved_frame = frame.copy()
            last_saved_index = frame_index

        frame_index += 1

        # Print progress every 2 seconds
        now = time.time()
        if now - last_progress_time >= 2.0:
            pct = (frame_index / info["total_frames"] * 100) if info["total_frames"] > 0 else 0
            elapsed = now - start_time
            fps_processing = frame_index / elapsed if elapsed > 0 else 0
            print(
                f"  Progress: {frame_index}/{info['total_frames']} frames "
                f"({pct:.1f}%) | {fps_processing:.0f} frames/sec | "
                f"{saved_count} saved"
            )
            last_progress_time = now

    # In scene-detect mode, always save the last frame if it wasn't already saved
    if scene_detect and last_frame is not None and last_saved_index != frame_index - 1:
        saved_count += 1
        filename = f"{prefix}_{saved_count:0{pad_width}d}.{fmt}"
        filepath = os.path.join(output_dir, filename)
        success = cv2.imwrite(filepath, last_frame, encode_params)
        if success:
            timestamp_sec = (frame_index - 1) / info["fps"] if info["fps"] > 0 else 0.0
            sim_final = compute_similarity(last_saved_frame, last_frame) if last_saved_frame is not None else 0.0
            manifest_entries.append({
                "filename": filename,
                "frame_index": frame_index - 1,
                "timestamp_sec": round(timestamp_sec, 3),
                "timestamp_fmt": format_duration(timestamp_sec),
                "similarity_to_previous": round(sim_final, 4),
            })

    cap.release()
    elapsed = time.time() - start_time

    # Summary
    print("=" * 60)
    print("Extraction complete!")
    print(f"  Frames read : {frame_index}")
    print(f"  Frames saved: {saved_count}")
    if scene_detect:
        reduction_pct = ((1 - saved_count / max(frame_index, 1)) * 100)
        print(f"  Reduction   : {reduction_pct:.1f}% fewer frames")
        if len(manifest_entries) >= 2:
            intervals = [
                manifest_entries[i]["frame_index"] - manifest_entries[i - 1]["frame_index"]
                for i in range(1, len(manifest_entries))
            ]
            avg_interval = sum(intervals) / len(intervals)
            print(f"  Avg interval: {avg_interval:.0f} frames between captures")
    print(f"  Output dir  : {os.path.abspath(output_dir)}")
    print(f"  Time elapsed: {elapsed:.2f}s")
    if elapsed > 0:
        print(f"  Speed       : {frame_index / elapsed:.0f} frames/sec")

    # Write manifest (always for scene-detect, or when explicitly requested)
    manifest_result_path = None
    if scene_detect or manifest_path:
        if manifest_path is None:
            manifest_path = os.path.join(output_dir, "manifest.json")
        manifest_data = {
            "video": {
                "path": os.path.abspath(input_path),
                "fps": info["fps"],
                "resolution": f"{info['width']}x{info['height']}",
                "duration_sec": round(info["duration_sec"], 3),
                "total_frames": info["total_frames"],
                "codec": info["codec"],
            },
            "extraction": {
                "mode": "scene-detect" if scene_detect else "every-n",
                "every_n": every_n,
                "threshold": threshold if scene_detect else None,
                "min_interval": min_interval if scene_detect else None,
                "format": fmt,
                "quality": quality if fmt == "jpg" else None,
                "frames_saved": saved_count,
                "frames_read": frame_index,
            },
            "frames": manifest_entries if manifest_entries else [
                {"filename": f"{prefix}_{i:0{pad_width}d}.{fmt}", "frame_index": (i - 1) * every_n}
                for i in range(1, saved_count + 1)
            ],
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        manifest_result_path = os.path.abspath(manifest_path)
        print(f"  Manifest    : {manifest_result_path}")

    print("=" * 60)

    return {
        "frames_read": frame_index,
        "frames_saved": saved_count,
        "output_dir": os.path.abspath(output_dir),
        "elapsed_sec": elapsed,
        "video_info": info,
        "manifest_path": manifest_result_path,
    }


def main() -> None:
    """Main entry point."""
    args = parse_args()
    validate_args(args)

    result = extract_frames(
        input_path=args.input,
        output_dir=args.output_dir,
        every_n=args.every_n,
        fmt=args.format,
        quality=args.quality,
        prefix=args.prefix,
        scene_detect=args.scene_detect,
        threshold=args.threshold,
        min_interval=args.min_interval,
        manifest_path=args.manifest,
    )

    # Exit with appropriate code
    if result["frames_saved"] == 0:
        print("Warning: No frames were saved.", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
