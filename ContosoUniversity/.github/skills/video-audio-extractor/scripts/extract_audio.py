#!/usr/bin/env python3
"""
video-audio-extractor — Extract audio from video and generate transcript.

Usage:
    # Full extraction + transcription
    python extract_audio.py --video demo.mp4 --output-dir ./output

    # With user-provided transcript (skips extraction)
    python extract_audio.py --transcript narration.srt --output-dir ./output

    # Specify whisper model and language
    python extract_audio.py --video demo.mp4 --output-dir ./output \
        --whisper-model medium --language en

Dependencies:
    - ffmpeg (system): https://ffmpeg.org/download.html
    - openai-whisper (pip): pip install openai-whisper
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SUPPORTED_VIDEO_FORMATS = {".mp4", ".avi", ".mkv", ".mov"}
SUPPORTED_TRANSCRIPT_FORMATS = {".srt", ".vtt", ".txt"}


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"


def probe_audio_stream(video_path: str) -> bool:
    """Check if video file contains an audio stream using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                video_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip() == "audio"
    except FileNotFoundError:
        print("ERROR: ffprobe not found. Install ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("WARNING: ffprobe timed out. Assuming audio track exists.")
        return True


def extract_audio(video_path: str, output_path: str) -> bool:
    """Extract audio from video to WAV (16kHz mono) using ffmpeg."""
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", video_path,
                "-vn",                    # No video
                "-acodec", "pcm_s16le",   # 16-bit PCM
                "-ar", "16000",           # 16kHz sample rate
                "-ac", "1",               # Mono
                "-y",                     # Overwrite
                output_path,
            ],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )
        if result.returncode != 0:
            print(f"WARNING: ffmpeg extraction failed: {result.stderr[:500]}")
            return False
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            print("WARNING: Extracted audio file is empty or missing.")
            return False
        return True
    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Install ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("WARNING: ffmpeg extraction timed out after 10 minutes.")
        return False


def transcribe_audio(audio_path: str, model_name: str = "base",
                     language: str = None) -> dict:
    """Transcribe audio using OpenAI Whisper."""
    try:
        import whisper
    except ImportError:
        print("ERROR: openai-whisper not installed. Run: pip install openai-whisper")
        sys.exit(1)

    print(f"Loading whisper model '{model_name}'...")
    model = whisper.load_model(model_name)

    print("Transcribing audio (this may take a while)...")
    transcribe_options = {"verbose": False}
    if language:
        transcribe_options["language"] = language

    result = model.transcribe(audio_path, **transcribe_options)

    segments = []
    for i, seg in enumerate(result.get("segments", []), start=1):
        segments.append({
            "id": i,
            "start": format_timestamp(seg["start"]),
            "end": format_timestamp(seg["end"]),
            "start_seconds": round(seg["start"], 2),
            "end_seconds": round(seg["end"], 2),
            "text": seg["text"].strip(),
        })

    # Calculate total duration from last segment
    duration = 0
    if segments:
        duration = int(segments[-1]["end_seconds"])

    detected_lang = result.get("language", language or "unknown")

    return {
        "source": "whisper",
        "model": model_name,
        "language": detected_lang,
        "duration_seconds": duration,
        "segments": segments,
    }


def parse_srt(file_path: str) -> dict:
    """Parse SRT subtitle file into transcript format."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    segments = []
    # SRT pattern: sequence number, timestamp line, text lines, blank line
    blocks = re.split(r"\n\s*\n", content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        # Find timestamp line
        ts_pattern = r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
        ts_match = None
        text_lines = []

        for line in lines:
            match = re.match(ts_pattern, line)
            if match:
                ts_match = match
            elif ts_match is not None:
                # Lines after the timestamp are text
                text_lines.append(line.strip())
            # Lines before timestamp (sequence number) are skipped

        if ts_match and text_lines:
            h1, m1, s1, ms1 = int(ts_match.group(1)), int(ts_match.group(2)), int(ts_match.group(3)), int(ts_match.group(4))
            h2, m2, s2, ms2 = int(ts_match.group(5)), int(ts_match.group(6)), int(ts_match.group(7)), int(ts_match.group(8))

            start_sec = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
            end_sec = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0

            segments.append({
                "id": len(segments) + 1,
                "start": format_timestamp(start_sec),
                "end": format_timestamp(end_sec),
                "start_seconds": round(start_sec, 2),
                "end_seconds": round(end_sec, 2),
                "text": " ".join(text_lines),
            })

    duration = int(segments[-1]["end_seconds"]) if segments else 0
    return {
        "source": "user-provided",
        "model": None,
        "language": None,
        "duration_seconds": duration,
        "segments": segments,
    }


def parse_vtt(file_path: str) -> dict:
    """Parse WebVTT file into transcript format."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove WEBVTT header and any STYLE blocks
    content = re.sub(r"WEBVTT.*?\n", "", content, count=1)
    content = re.sub(r"STYLE\s*\n.*?\n\n", "", content, flags=re.DOTALL)

    segments = []
    blocks = re.split(r"\n\s*\n", content.strip())

    ts_pattern = r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"

    for block in blocks:
        lines = block.strip().split("\n")
        ts_match = None
        text_lines = []

        for line in lines:
            match = re.match(ts_pattern, line)
            if match:
                ts_match = match
            elif ts_match is not None and not line.startswith("NOTE"):
                cleaned = re.sub(r"<[^>]+>", "", line.strip())  # Strip VTT tags
                if cleaned:
                    text_lines.append(cleaned)

        if ts_match and text_lines:
            h1, m1, s1, ms1 = int(ts_match.group(1)), int(ts_match.group(2)), int(ts_match.group(3)), int(ts_match.group(4))
            h2, m2, s2, ms2 = int(ts_match.group(5)), int(ts_match.group(6)), int(ts_match.group(7)), int(ts_match.group(8))

            start_sec = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
            end_sec = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0

            segments.append({
                "id": len(segments) + 1,
                "start": format_timestamp(start_sec),
                "end": format_timestamp(end_sec),
                "start_seconds": round(start_sec, 2),
                "end_seconds": round(end_sec, 2),
                "text": " ".join(text_lines),
            })

    duration = int(segments[-1]["end_seconds"]) if segments else 0
    return {
        "source": "user-provided",
        "model": None,
        "language": None,
        "duration_seconds": duration,
        "segments": segments,
    }


def parse_txt(file_path: str) -> dict:
    """Parse plain text file into transcript format.

    If lines contain timestamp patterns like [MM:SS] or (MM:SS), they are
    parsed as segment boundaries. Otherwise, the entire file is treated as
    a single segment starting at 00:00.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    segments = []

    # Check if any line has timestamps
    ts_pattern = r"[\[\(](?:(\d{1,2}):)?(\d{1,2}):(\d{2})[\]\)]"
    has_timestamps = any(re.search(ts_pattern, line) for line in lines)

    if has_timestamps:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = re.search(ts_pattern, line)
            if match:
                hours = int(match.group(1)) if match.group(1) else 0
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                start_sec = hours * 3600 + minutes * 60 + seconds

                # Remove the timestamp from text
                text = re.sub(ts_pattern, "", line).strip()
                if text:
                    segments.append({
                        "id": len(segments) + 1,
                        "start": format_timestamp(start_sec),
                        "end": "",  # Will be filled in post-processing
                        "start_seconds": round(start_sec, 2),
                        "end_seconds": 0,
                        "text": text,
                    })

        # Fill in end times from next segment's start
        for i in range(len(segments) - 1):
            segments[i]["end_seconds"] = segments[i + 1]["start_seconds"]
            segments[i]["end"] = format_timestamp(segments[i]["end_seconds"])
        if segments:
            # Last segment: end = start + 10 seconds (estimate)
            segments[-1]["end_seconds"] = segments[-1]["start_seconds"] + 10
            segments[-1]["end"] = format_timestamp(segments[-1]["end_seconds"])
    else:
        # No timestamps — treat as single segment
        full_text = " ".join(line.strip() for line in lines if line.strip())
        if full_text:
            segments.append({
                "id": 1,
                "start": "00:00",
                "end": "00:00",
                "start_seconds": 0,
                "end_seconds": 0,
                "text": full_text,
            })

    duration = int(segments[-1]["end_seconds"]) if segments else 0
    return {
        "source": "user-provided",
        "model": None,
        "language": None,
        "duration_seconds": duration,
        "segments": segments,
    }


def parse_user_transcript(transcript_path: str) -> dict:
    """Parse user-provided transcript file based on extension."""
    ext = Path(transcript_path).suffix.lower()

    if ext == ".srt":
        return parse_srt(transcript_path)
    elif ext == ".vtt":
        return parse_vtt(transcript_path)
    elif ext == ".txt":
        return parse_txt(transcript_path)
    else:
        print(f"ERROR: Unsupported transcript format '{ext}'. "
              f"Supported: {', '.join(SUPPORTED_TRANSCRIPT_FORMATS)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Extract audio from video and generate timestamped transcript.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --video demo.mp4 --output-dir ./output
  %(prog)s --transcript narration.srt --output-dir ./output
  %(prog)s --video demo.mp4 --output-dir ./output --whisper-model medium
        """,
    )
    parser.add_argument("--video", help="Path to video file (MP4/AVI/MKV/MOV)")
    parser.add_argument("--transcript", help="Path to user-provided transcript (TXT/SRT/VTT)")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--whisper-model", default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--language", default=None,
                        help="Language hint for whisper (ISO 639-1 code, e.g., 'en')")
    args = parser.parse_args()

    # Validate inputs
    if not args.video and not args.transcript:
        parser.error("Either --video or --transcript must be provided.")

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    transcript_output = os.path.join(args.output_dir, "transcript.json")

    # ── Path A: User-provided transcript ──
    if args.transcript:
        if not os.path.exists(args.transcript):
            print(f"ERROR: Transcript file not found: {args.transcript}")
            sys.exit(1)

        ext = Path(args.transcript).suffix.lower()
        if ext not in SUPPORTED_TRANSCRIPT_FORMATS:
            print(f"ERROR: Unsupported transcript format '{ext}'. "
                  f"Supported: {', '.join(SUPPORTED_TRANSCRIPT_FORMATS)}")
            sys.exit(1)

        print(f"Parsing user-provided transcript: {args.transcript}")
        transcript = parse_user_transcript(args.transcript)
        print(f"Parsed {len(transcript['segments'])} segments.")

        with open(transcript_output, "w", encoding="utf-8") as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)
        print(f"Transcript saved to: {transcript_output}")
        return

    # ── Path B: Extract from video ──
    video_path = args.video
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        sys.exit(1)

    ext = Path(video_path).suffix.lower()
    if ext not in SUPPORTED_VIDEO_FORMATS:
        print(f"ERROR: Unsupported video format '{ext}'. "
              f"Supported: {', '.join(SUPPORTED_VIDEO_FORMATS)}")
        sys.exit(1)

    # Phase 1: Probe audio
    print(f"Probing audio in: {video_path}")
    has_audio = probe_audio_stream(video_path)
    if not has_audio:
        print("WARNING: Video has no audio track. Skipping audio extraction.")
        empty_transcript = {
            "source": "none",
            "model": None,
            "language": None,
            "duration_seconds": 0,
            "segments": [],
        }
        with open(transcript_output, "w", encoding="utf-8") as f:
            json.dump(empty_transcript, f, indent=2, ensure_ascii=False)
        print(f"Empty transcript saved to: {transcript_output}")
        return

    # Phase 2: Extract audio
    audio_path = os.path.join(args.output_dir, "audio.wav")
    print(f"Extracting audio to: {audio_path}")
    success = extract_audio(video_path, audio_path)
    if not success:
        print("WARNING: Audio extraction failed. Creating empty transcript.")
        empty_transcript = {
            "source": "extraction-failed",
            "model": None,
            "language": None,
            "duration_seconds": 0,
            "segments": [],
        }
        with open(transcript_output, "w", encoding="utf-8") as f:
            json.dump(empty_transcript, f, indent=2, ensure_ascii=False)
        return

    audio_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"Audio extracted: {audio_size_mb:.1f} MB")

    # Warn for long audio files
    if audio_size_mb > 50:
        print("NOTE: Large audio file detected. Transcription may take several minutes on CPU.")

    # Phase 3: Transcribe
    transcript = transcribe_audio(audio_path, args.whisper_model, args.language)
    print(f"Transcribed {len(transcript['segments'])} segments, "
          f"duration: {format_timestamp(transcript['duration_seconds'])}")

    with open(transcript_output, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, ensure_ascii=False)
    print(f"Transcript saved to: {transcript_output}")


if __name__ == "__main__":
    main()
