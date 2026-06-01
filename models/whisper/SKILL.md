---
name: whisper
description: OpenAI's general-purpose speech recognition model. Supports 99 languages, transcription, translation to English, and language identification. Six model sizes from tiny (39M params) to large (1550M params). Use for speech-to-text, podcast transcription, or multilingual audio processing. Best for robust, multilingual ASR.
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [openai-whisper, transformers, torch]
metadata:
  hermes:
    tags: [Whisper, Speech Recognition, ASR, Multimodal, Multilingual, OpenAI, Speech-To-Text, Transcription, Translation, Audio Processing]

---

# Whisper - Robust Speech Recognition

OpenAI's multilingual speech recognition model.

## When to use Whisper

**Use when:**
- Speech-to-text transcription (99 languages)
- Podcast/video transcription
- Meeting notes automation
- Translation to English
- Noisy audio transcription
- Multilingual audio processing

**Metrics**:
- **72,900+ GitHub stars**
- 99 languages supported
- Trained on 680,000 hours of audio
- MIT License

**Use alternatives instead**:
- **AssemblyAI**: Managed API, speaker diarization
- **Deepgram**: Real-time streaming ASR
- **Google Speech-to-Text**: Cloud-based

## Quick start

### Installation

```bash
# Requires Python 3.8-3.11 and ffmpeg

# DO NOT use pip directly in hermes-agent venv — venv has no pip module
# Use uv instead (available at ~/.local/bin/uv or system-wide):

uv venv /home/lxgxdx/whisper-venv --python 3.11
uv pip install --python /home/lxgxdx/whisper-venv/bin/python openai-whisper

# Activate before use:
source /home/lxgxdx/whisper-venv/bin/activate

# Requires ffmpeg:
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: choco install ffmpeg
```

**Pitfall — venv pip module missing:** If `python3 -m pip` fails with `No module named pip`, the venv was created without pip. Recreate with `uv venv` above. Do NOT try to `pip install pip` or modify the venv — just recreate it.

**Pitfall — model download on first load:** `whisper.load_model()` downloads the model (~461MB for `small`) on first run. This can take 1-2 minutes on slow connections — this is normal, not a hang.

### Basic transcription

```python
import whisper

# Load model
model = whisper.load_model("base")

# Transcribe
result = model.transcribe("audio.mp3")

# Print text
print(result["text"])

# Access segments
for segment in result["segments"]:
    print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}")
```

## Model sizes

```python
# Available models
models = ["tiny", "base", "small", "medium", "large", "turbo"]

# Load specific model
model = whisper.load_model("turbo")  # Fastest, good quality
```

| Model | Parameters | English-only | Multilingual | Speed | VRAM |
|-------|------------|--------------|--------------|-------|------|
| tiny | 39M | ✓ | ✓ | ~32x | ~1 GB |
| base | 74M | ✓ | ✓ | ~16x | ~1 GB |
| small | 244M | ✓ | ✓ | ~6x | ~2 GB |
| medium | 769M | ✓ | ✓ | ~2x | ~5 GB |
| large | 1550M | ✗ | ✓ | 1x | ~10 GB |
| turbo | 809M | ✗ | ✓ | ~8x | ~6 GB |

**Recommendation**: Use `turbo` for best speed/quality, `base` for prototyping

## Transcription options

### Chinese government meeting transcription

Government meetings involve multiple speakers, formal vocabulary, and policy terminology.
Supplying a domain-specific `initial_prompt` dramatically improves accuracy:

```python
result = model.transcribe(
    "meeting.wav",
    language="zh",
    initial_prompt=(
        "这是一段政府部务会会议录音，与会人员包括多位领导干部，"
        "讨论统战工作相关议题。"
    )
)
```

**Chinese meeting transcription workflow:**
1. Pre-check audio duration with `ffprobe -v quiet -show_entries format=duration -of csv=p=0 file.wav`
2. Files <1 min may be truncated/incomplete — check size before processing
3. Long files (>30 min) may degrade; consider splitting with `ffmpeg -i in.wav -ss 0 -t 3600 part1.wav -ss 3600 part2.wav`
4. Use `small` model for Chinese (good quality/speed balance on CPU)
5. Output raw text first, then use an LLM to structure into meeting minutes format

### Task selection

```python
# Transcription (default)
result = model.transcribe("audio.mp3", task="transcribe")

# Translation to English
result = model.transcribe("spanish.mp3", task="translate")
# Input: Spanish audio → Output: English text
```

### Initial prompt

```python
# Improve accuracy with context
result = model.transcribe(
    "audio.mp3",
    initial_prompt="This is a technical podcast about machine learning and AI."
)

# Helps with:
# - Technical terms
# - Proper nouns
# - Domain-specific vocabulary
```

### Quick file inspection before transcribing

```bash
# Check duration — files <5 seconds are truncated, skip them
ffprobe -v quiet -show_entries format=duration -of csv=p=0 file.wav
# Check audio quality
ffprobe -v quiet -show_entries stream=channels,sample_rate,codec_name -of csv=p=0 file.wav
# Check volume levels
ffmpeg -i file.wav -af volumedetect -f null /dev/null 2>&1 | grep -E "max_volume|mean_volume"
```

**Heuristics:**
- <5 seconds → truncated/invalid, skip
- ADPCM codec (adpcm_ms) → low quality, expect poor accuracy with small model
- mean_volume < -25 dB → too quiet, preprocess with volume boost
- audio check is essential before starting a long transcription; a 60-minute transcription failing due to a bad file wastes an hour

### Timestamps

```python
# Word-level timestamps
result = model.transcribe("audio.mp3", word_timestamps=True)

for segment in result["segments"]:
    for word in segment["words"]:
        print(f"{word['word']} ({word['start']:.2f}s - {word['end']:.2f}s)")
```

### Temperature fallback

```python
# Retry with different temperatures if confidence low
result = model.transcribe(
    "audio.mp3",
    temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
)
```

## Command line usage

```bash
# Basic transcription
whisper audio.mp3

# Specify model
whisper audio.mp3 --model turbo

# Output formats
whisper audio.mp3 --output_format txt     # Plain text
whisper audio.mp3 --output_format srt     # Subtitles
whisper audio.mp3 --output_format vtt     # WebVTT
whisper audio.mp3 --output_format json    # JSON with timestamps

# Language
whisper audio.mp3 --language Spanish

# Translation
whisper spanish.mp3 --task translate
```

## Batch processing

```python
import os

audio_files = ["file1.mp3", "file2.mp3", "file3.mp3"]

for audio_file in audio_files:
    print(f"Transcribing {audio_file}...")
    result = model.transcribe(audio_file)

    # Save to file
    output_file = audio_file.replace(".mp3", ".txt")
    with open(output_file, "w") as f:
        f.write(result["text"])
```

## CPU-optimized transcription (faster-whisper)

For CPU-based transcription (no GPU), **always use faster-whisper** instead of openai-whisper.
It supports int8 quantization and runs 4× faster with comparable accuracy.

```bash
uv pip install faster-whisper
```

```python
from faster_whisper import WhisperModel

# CPU optimized — int8 gives 4× speedup over openai-whisper float32
model = WhisperModel("medium", device="cpu", compute_type="int8")

segments, info = model.transcribe("audio.wav", language="zh")

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

### Recommended models by use case (CPU only)

| Scenario | Model | faster-whisper compute_type | Notes |
|----------|-------|----------------------------|-------|
| Quick test / short clip | `tiny` or `base` | int8 | ~instant |
| English podcast/lecture | `small` | int8 | Good balance |
| **Chinese meeting (low quality)** | **`medium`** | **int8** | **Minimum for government/formal context** |
| Chinese meeting (clean audio) | `small` | int8 | Acceptable with initial_prompt |
| Max accuracy (any language) | `large-v3` | int8 | Slow but best |

**Critical finding — Chinese government meeting audio:** Low-bitrate WAV files (ADPCM, 32kHz mono) produce extremely poor results with `small` model — names, policy terms, and numbers are consistently misrecognized. `medium` int8 is the practical minimum for usable quality. Even with medium, expect ~70-80% accuracy; use an LLM pass to correct terminology afterward.

### Audio preprocessing (required for low-quality recordings)

Before transcribing low-bitrate or noisy audio, always normalize and resample:

```bash
ffmpeg -y -i original.wav \
  -af "highpass=f=200,lowpass=f=8000,volume=1.5,alimiter=limit=0.95" \
  -ar 16000 -ac 1 -acodec pcm_s16le \
  output_norm.wav
```

The filter chain: highpass removes rumble (f=200), lowpass removes high-frequency noise (f=8000), volume boosts quiet speech, alimiter prevents clipping. Output: 16kHz mono PCM — Whisper's optimal input.

## Real-time transcription

```python
# For streaming audio, use faster-whisper
# pip install faster-whisper

from faster_whisper import WhisperModel

model = WhisperModel("base", device="cuda", compute_type="float16")

# Transcribe with streaming
segments, info = model.transcribe("audio.mp3", beam_size=5)

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

## GPU acceleration

```python
import whisper

# Automatically uses GPU if available
model = whisper.load_model("turbo")

# Force CPU
model = whisper.load_model("turbo", device="cpu")

# Force GPU
model = whisper.load_model("turbo", device="cuda")

# 10-20× faster on GPU
```

## Integration with other tools

### Subtitle generation

```bash
# Generate SRT subtitles
whisper video.mp4 --output_format srt --language English

# Output: video.srt
```

### With LangChain

```python
from langchain.document_loaders import WhisperTranscriptionLoader

loader = WhisperTranscriptionLoader(file_path="audio.mp3")
docs = loader.load()

# Use transcription in RAG
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

vectorstore = Chroma.from_documents(docs, OpenAIEmbeddings())
```

### Extract audio from video

```bash
# Use ffmpeg to extract audio
ffmpeg -i video.mp4 -vn -acodec pcm_s16le audio.wav

# Then transcribe
whisper audio.wav
```

## Best practices

1. **Use turbo model** - Best speed/quality for English
2. **Specify language** - Faster than auto-detect
3. **Add initial prompt** - Improves technical terms
4. **Use GPU** - 10-20× faster
5. **Batch process** - More efficient
6. **Convert to WAV** - Better compatibility
7. **Split long audio** - <30 min chunks
8. **Check language support** - Quality varies by language
9. **Use faster-whisper** - 4× faster than openai-whisper
10. **Monitor VRAM** - Scale model size to hardware

## Performance

| Model | Real-time factor (CPU) | Real-time factor (GPU) |
|-------|------------------------|------------------------|
| tiny | ~0.32 | ~0.01 |
| base | ~0.16 | ~0.01 |
| turbo | ~0.08 | ~0.01 |
| large | ~1.0 | ~0.05 |

*Real-time factor: 0.1 = 10× faster than real-time*

## Language support

Top-supported languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)

Full list: 99 languages total

## Limitations

1. **Hallucinations** - May repeat or invent text
2. **Long-form accuracy** - Degrades on >30 min audio
3. **Speaker identification** - No diarization
4. **Accents** - Quality varies
5. **Background noise** - Can affect accuracy
6. **Real-time latency** - Not suitable for live captioning

## Resources

- **GitHub**: https://github.com/openai/whisper ⭐ 72,900+
- **Paper**: https://arxiv.org/abs/2212.04356
- **Model Card**: https://github.com/openai/whisper/blob/main/model-card.md
- **Colab**: Available in repo
- **License**: MIT


