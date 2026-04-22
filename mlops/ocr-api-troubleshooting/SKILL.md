---
name: ocr-api-troubleshooting
description: Troubleshooting guide for OCR API failures when health check passes but OCR returns 500 Internal Server Error. Focuses on EasyOCR GPU deployment issues.
tags: [ocr, easyocr, api, troubleshooting, docker, gpu]
category: mlops
---

# OCR API Troubleshooting Guide

## Problem Pattern
- Health check endpoint (`/health`) returns `{"status":"ok"}` (200 OK)
- OCR endpoints (`/ocr` or `/ocr/base64`) return "Internal Server Error" (500)
- No access to container logs (SSH unavailable)

## Diagnostic Workflow

### Step 1: Verify API Connectivity
```bash
# Test health endpoint
curl http://[SERVER_IP]:[PORT]/health

# Test both OCR endpoints with a simple test image
# Create test image
convert -size 200x50 xc:white -pointsize 20 -fill black \
  -draw "text 10,30 'Test Text'" /tmp/test_ocr.png

# Test multipart endpoint
curl -X POST http://[SERVER_IP]:[PORT]/ocr \
  -F "languages=en" \
  -F "image=@/tmp/test_ocr.png"

# Test base64 endpoint  
base64 -w0 /tmp/test_ocr.png > /tmp/test_base64.txt
curl -X POST http://[SERVER_IP]:[PORT]/ocr/base64 \
  -d "image_data=$(cat /tmp/test_base64.txt)" \
  -d "languages=en" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

### Step 2: Check API Documentation
```bash
# Verify API is properly documented
curl http://[SERVER_IP]:[PORT]/docs      # Swagger UI
curl http://[SERVER_IP]:[PORT]/openapi.json  # OpenAPI spec
```

## Common Root Causes

### 1. GPU Access Failure (Most Common with EasyOCR)
**Symptoms**: Container starts, health check passes, but OCR fails when `gpu=True`
**Root Cause**: 
- CUDA driver mismatch
- NVIDIA Container Toolkit not installed/configured
- Insufficient GPU memory
- Permission issues

**Diagnostic Commands (if container access available):**
```bash
# Check GPU visibility
nvidia-smi

# Check PyTorch CUDA availability
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
python -c "import torch; print('CUDA version:', torch.version.cuda)"

# Check EasyOCR installation
python -c "import easyocr; print('EasyOCR version:', easyocr.__version__)"
```

**Solution**: Switch to CPU mode as temporary fix
1. Modify `api.py` to use `gpu=False` in `easyocr.Reader()` initialization
2. Rebuild container with `--no-cache` flag
3. Restart container

### 2. Model Download Failure
**Symptoms**: First-time startup hangs or times out
**Root Cause**: Network issues downloading model files
**Solution**:
1. Increase startup timeout in Docker Compose
2. Pre-download models to cache volume
3. Use smaller language models initially

### 3. Insufficient GPU Memory
**Symptoms**: Works with small images, fails with larger ones
**Root Cause**: Other services (like Infinity vector service) consuming GPU memory
**Diagnostic**: Check `nvidia-smi` for memory usage
**Solution**:
1. Stop competing GPU services temporarily
2. Reduce batch size in OCR processing
3. Use CPU mode (`gpu=False`)

### 4. CUDA Version Mismatch
**Symptoms**: PyTorch compiled for different CUDA version than host
**Diagnostic**:
```bash
# In container
python -c "import torch; print(torch.version.cuda)"

# On host
nvidia-smi | grep CUDA
```

**Solution**: Use Docker image with matching CUDA version

## Emergency Fix Procedure

### When SSH/Container Access is Unavailable

1. **Stop the container** via management interface (Unraid Web UI, Portainer, etc.)
2. **Modify configuration file**:
   - Locate `api.py` in mounted volume
   - Change `gpu=True` to `gpu=False` in `easyocr.Reader()` call
3. **Rebuild container**:
   ```bash
   cd /path/to/ocr/project
   docker build --no-cache -t ocr-service:latest .
   ```
4. **Restart container**
5. **Verify fix**:
   ```bash
   curl http://[SERVER_IP]:[PORT]/health
   curl -X POST http://[SERVER_IP]:[PORT]/ocr -F "image=@test.png"
   ```

## Prevention Strategies

### 1. Implement Graceful Degradation
```python
# In api.py initialization
try:
    reader = easyocr.Reader(["en"], gpu=True, verbose=False)
    print("✅ EasyOCR ready (GPU mode)")
except Exception as e:
    print(f"⚠️ GPU mode failed: {e}, falling back to CPU")
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    print("✅ EasyOCR ready (CPU fallback mode)")
```

### 2. Add Diagnostic Endpoints
```python
@app.get("/diagnostics")
async def diagnostics():
    """Return system diagnostics"""
    import torch
    return {
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "easyocr_version": easyocr.__version__,
    }
```

### 3. Comprehensive Health Check
```python
@app.get("/health")
async def health():
    """Comprehensive health check including OCR functionality"""
    try:
        # Test OCR with a simple generated image
        test_result = reader.readtext(test_image, detail=0)
        return {
            "status": "healthy",
            "ocr_working": True,
            "gpu_mode": reader.gpu
        }
    except Exception as e:
        return {
            "status": "degraded",
            "ocr_working": False,
            "error": str(e),
            "gpu_mode": reader.gpu
        }
```

## Related Skills
- `easyocr-unraid-p4-deploy` - Deployment guide for EasyOCR on Unraid Tesla P4
- `minimax-dspy-evolution-fix` - API integration troubleshooting
- `unraid-p4-ocr-deploy` - General OCR deployment on Unraid P4

## Key Takeaways
1. **Health check passing ≠ OCR working** - Need functional tests
2. **GPU failures are silent** - EasyOCR doesn't always raise clear errors
3. **CPU fallback is essential** for production reliability
4. **Remote debugging requires creative approaches** when direct access is unavailable