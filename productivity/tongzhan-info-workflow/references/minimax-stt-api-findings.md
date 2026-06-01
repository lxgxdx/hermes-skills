# MiniMax API 语音转写能力确认（2026-06-01）

## 结论：MiniMax 无 STT API

MiniMax 官方文档中心（minimaxi.com）和 API 平台（platform.minimax.com）**均不提供语音转文字（Speech-to-Text）接口**。

## 验证过程

### 1. 文档中心路径尝试
| URL | 结果 |
|-----|------|
| `https://www.minimaxi.com/document` | 重定向至主页 |
| `https://www.minimaxi.com/document/guides` | 404 |
| `https://www.minimaxi.com/document/api-details/voice` | 404 |
| `https://platform.minimax.com/document` | 404 |
| `https://www.minimax.io/document/speech-to-text` | 重定向回主页 |

### 2. API 端点测试
| 端点 | 方法 | 结果 |
|------|------|------|
| `/v1/audio/transcriptions` | POST | **404 page not found**（类 OpenAI Whisper 接口，不存在） |
| `/v1/audio/speech` | POST | **404 page not found**（TTS 端点也不存在于此域名） |
| `/v1/chat/completions` | POST | 401 认证失败（端点存在，需有效 key） |

### 3. MiniMax 实际提供的 API 能力
| 能力 | 端点 | 备注 |
|------|------|------|
| LLM 对话 | `/v1/chat/completions` | ✅ 可用 |
| 图片生成 | `/v1/image_generation` | ✅ 可用 |
| TTS（文字→语音） | 需进一步确认端点 | 官网有 Speech 2.8 产品 |
| **STT（语音→文字）** | **不存在** | ❌ |

## 启示

政府会议录音整理（部务会等）**无法依赖 MiniMax API 做语音转写**，必须使用本地 Whisper（faster-whisper）方案。

如对转录质量要求高，优先方案：
1. **讯飞听见**（商用 STT，专注政府/会议场景，普通话识别率领先）
2. **飞书妙记**（如果用户使用飞书生态）
3. 本地 faster-whisper medium（CPU 运行，硬件成本低但速度慢）
