# Supported Formats — video-audio-extractor

## Video Input Formats

| Format | Extension | Container | Notes |
|--------|-----------|-----------|-------|
| MPEG-4 | `.mp4` | MP4 | Most common. AAC or MP3 audio tracks |
| AVI | `.avi` | AVI | Legacy format. PCM or MP3 audio |
| Matroska | `.mkv` | MKV | Flexible container. May have multiple audio tracks |
| QuickTime | `.mov` | MOV | Apple ecosystem. AAC audio typical |

### Audio Codec Support

ffmpeg handles all common audio codecs found in these containers:
- AAC (most common in MP4/MOV)
- MP3
- PCM/WAV (uncompressed)
- Vorbis (common in MKV)
- Opus (common in MKV/WebM)
- FLAC (lossless, sometimes in MKV)
- AC3/EAC3 (common in AVI)

### Multiple Audio Tracks

When a video contains multiple audio tracks (common in MKV), the script
extracts the **first audio stream** (`-map 0:a:0`). To extract a specific
track, modify the ffmpeg command with `-map 0:a:{track_index}`.

---

## Transcript Input Formats

When providing a user transcript instead of extracting audio, these formats
are supported:

### SRT (SubRip Subtitle)

```
1
00:00:05,000 --> 00:00:12,000
Now I'm going to show you how to create a new vehicle

2
00:00:12,000 --> 00:00:18,000
First we need to fill in the vehicle name and select the type
```

**Parsing rules**:
- Each block starts with a sequence number (ignored)
- Timestamp format: `HH:MM:SS,mmm --> HH:MM:SS,mmm`
- Text lines follow until blank line
- Multi-line text within a block is joined with spaces

### VTT (WebVTT)

```
WEBVTT

00:00:05.000 --> 00:00:12.000
Now I'm going to show you how to create a new vehicle

00:00:12.000 --> 00:00:18.000
First we need to fill in the vehicle name and select the type
```

**Parsing rules**:
- Must start with `WEBVTT` header (skipped)
- Timestamp format: `HH:MM:SS.mmm --> HH:MM:SS.mmm`
- Optional cue identifiers (ignored)
- Style blocks (`::cue`, `STYLE`) are ignored

### TXT (Plain Text)

```
[00:05] Now I'm going to show you how to create a new vehicle
[00:12] First we need to fill in the vehicle name and select the type
```

**Parsing rules**:
- If lines contain timestamp patterns (`[MM:SS]`, `[HH:MM:SS]`, or
  `(MM:SS)`), parse them as segment boundaries
- If no timestamps found, treat entire file as a single segment starting
  at `00:00`
- Empty lines are treated as segment separators when no timestamps present

---

## Audio Output Format

The extracted audio is always converted to a standardized format for
consistent whisper processing:

| Property | Value | Reason |
|----------|-------|--------|
| Format | WAV (PCM) | Uncompressed for whisper compatibility |
| Sample Rate | 16,000 Hz | Whisper's native rate — avoids resampling |
| Channels | 1 (Mono) | Speech recognition doesn't need stereo |
| Bit Depth | 16-bit | Standard for speech processing |
| Encoding | Signed Little-Endian | `pcm_s16le` codec |

### File Size Estimates

| Video Duration | Approx. WAV Size |
|---------------|-----------------|
| 1 minute | ~1.9 MB |
| 5 minutes | ~9.4 MB |
| 15 minutes | ~28 MB |
| 30 minutes | ~56 MB |
| 1 hour | ~112 MB |

---

## Whisper Model Selection Guide

| Model | Size | Speed (CPU) | Speed (GPU) | Accuracy | Use Case |
|-------|------|-------------|-------------|----------|----------|
| `tiny` | 39M | ~10x realtime | ~32x | Low | Quick test, clear speech |
| `base` | 74M | ~7x realtime | ~30x | Medium | **Default** — good balance |
| `small` | 244M | ~4x realtime | ~24x | Good | Accented speech, some noise |
| `medium` | 769M | ~2x realtime | ~16x | High | Noisy environment, technical terms |
| `large` | 1550M | ~1x realtime | ~8x | Highest | Critical accuracy, multiple languages |

**Recommendation**: Use `base` for pipeline speed. Upgrade to `small` or
`medium` if transcript quality is poor on first run.
