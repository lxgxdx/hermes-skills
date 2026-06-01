# Meeting Minutes from Audio Transcription

Workflow: raw audio → whisper → raw text → LLM restructure → Word docx (公文格式)

## Full Pipeline

### Step 1: Audio Inspection & Preprocessing

```bash
# Check file quality before processing
ffprobe -v quiet -show_entries stream=channels,sample_rate,codec_name -of csv=p=0 file.wav
ffprobe -v quiet -show_entries format=duration -of csv=p=0 file.wav

# Normalize and clean low-quality audio
ffmpeg -y -i original.wav \
  -af "highpass=f=200,lowpass=f=8000,volume=1.5,alimiter=limit=0.95" \
  -ar 16000 -ac 1 -acodec pcm_s16le \
  output_norm.wav
```

Files <5 seconds are truncated — skip them. ADPCM codec + 32kHz mono = poor accuracy with small models, use medium.

### Step 2: Transcribe with faster-whisper (background job)

```bash
source /home/lxgxdx/whisper-venv/bin/activate
```

Write a Python script to file (to avoid execute_code Chinese char issues), then run with background=true:

Script template (save as `/tmp/transcribe.py`):
```python
from faster_whisper import WhisperModel
model = WhisperModel("medium", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    "/tmp/audio_norm.wav",
    language="zh",
    initial_prompt="这是一段政府部务会会议录音，与会人员包括多位领导干部，讨论统战工作相关议题。"
)
text = "".join(seg.text for seg in segments)
with open("/home/lxgxdx/transcript.txt", "w", encoding="utf-8") as f:
    f.write(text)
print(f"Done. {len(text)} chars")
```

Run: `terminal(background=true, command="...source venv && python3 /tmp/transcribe.py")`

### Step 3: LLM Restructure (correct errors + format)

After transcription, feed the raw text to the LLM with this prompt:

```
以下是会议录音的智能语音识别转写文本。请完成以下任务：

1. 纠正转写中的错别字和误识别（特别是人名、地名、政策术语、数字）
2. 按会议议题分段，每个议题加标题（一、XXX / 二、XXX）
3. 为每段标注发言人（如无法区分，标注"与会人员"）
4. 在开头加：会议时间、会议地点、参会人员、主持人、记录人
5. 在末尾加：会议总结、议定事项
6. 保持原意，不添加转写中未出现的内容

转写文本：
{raw_text}
```

### Step 4: Generate Word Document (公文格式)

Use `document-editor` skill. Key formatting:

```python
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

doc = Document()

# Page setup (A4, government standard margins)
for section in doc.sections:
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(3.7)
    section.bottom_margin = Cm(3.5)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.6)

def add_body(doc, text, bold=False):
    """仿宋三号，首行缩进2字符，28磅行距"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0.74)
    pf.line_spacing = Pt(28)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    run = p.add_run(text)
    run.font.name = '仿宋_GB2312'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '仿宋_GB2312')
    run.font.size = Pt(16)
    run.bold = bold
    return p

def add_section_title(doc, text):
    """黑体三号"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0.74)
    pf.line_spacing = Pt(28)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    run = p.add_run(text)
    run.font.name = '黑体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    run.font.size = Pt(16)
    return p

def add_title(doc, text):
    """标题：黑体二号居中"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.name = '黑体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    run.font.size = Pt(22)
    run.bold = True
    return p

# Save
doc.save("/mnt/nfs/2026年统战工作/会议记录/XXX.docx")
```

## Output path convention

For TZB documents:
```
/mnt/nfs/2026年统战工作/1.办公室/9.部务会/{date}/会议记录.docx
```

## Pitfalls

- **Never use `execute_code` for Chinese text with python-docx** — the sandbox parser rejects Chinese punctuation. Always `write_file` the script then `terminal` to run it.
- **file-size vs duration heuristics**: 55MB ≈ 1 hour for ADPCM WAV. Check actual duration with ffprobe before deciding to transcribe.
- **Background timeout**: A 600s timeout may expire for medium model on CPU; use notify_on_complete and check the error log at `/tmp/transcribe_NN_err.log`.
- **Two passes**: small model → session-specific poor quality → restart with medium. Check first 800 chars of output before committing to the full run.
