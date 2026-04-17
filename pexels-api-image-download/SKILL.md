---
name: pexels-api-image-download
description: 使用Pexels API搜索和下载高清图片，为PPT/文档获取配图。绕过网页Bot防护的直接API方案。
category: media
tags: [ppt, image, pexels, python]
created: 2026-04-16
---

# Pexels API 图片下载

## 触发条件
用户需要为PPT/文档获取高清图片，或者要求从Pexels搜索图片。

## 核心经验
- Pexels网页（pexels.com）有严格的Bot防护，curl/wget/Selenium均被拦截
- **正确方案：使用Pexels API**，用户需先注册 https://www.pexels.com/api/
- API Key注册后可直接使用，无需额外SDK

## API基础用法

```bash
# 搜索图片（返回JSON，含原图URL）
curl -s "https://api.pexels.com/v1/search?query=office+meeting&per_page=10" \
  -H "Authorization: YOUR_API_KEY"

# 下载图片（从search结果中取photo→src→original）
curl -L -o output.jpg "https://images.pexels.com/photos/PHOTO_ID/pexels-photo-PHOTO_ID.jpeg?auto=compress&cs=tinysrgb&w=1260"
```

## Python下载脚本
见 `scripts/download_pexels.py`（运行前设置环境变量或修改脚本内API_KEY）

## 已知限制
- API免费版：每月最多200次请求，每次最多50个结果
- `?auto=compress&cs=tinysrgb&w=1260` 等查询参数可压缩图片大小
- Pexels要求使用时在图片附近标注"Photo by XXX on Pexels"（免费版要求）
- 下载的图片仅在本工具内使用，不对外传播时无需额外授权

## 验证
```bash
curl -s "https://api.pexels.com/v1/search?query=office&per_page=1" \
  -H "Authorization: YOUR_API_KEY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('可用' if d.get('photos') else '无效')"
```
