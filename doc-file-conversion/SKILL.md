---
name: doc-file-conversion
description: 读取旧版 .doc 文件（Office 97-2003 二进制格式）的方法，用 libreoffice 转换为 txt。
category: productivity
---

# 旧版 .doc 文件读取方法

## 问题
python-docx 只能读 `.docx`（Office 2007+），无法读取老格式 `.doc`（Office 97-2003 二进制格式），会报 `PackageNotFoundError`。

## 解决方案
使用服务器上已有的 `libreoffice` 转换为 txt：

```bash
libreoffice --headless --convert-to txt "文件名.doc"
# 输出同名 .txt 文件
```

## 验证方法
```bash
file "文件名.doc"
# 输出含 "Composite Document File V2 Document" 则为旧格式
# 输出含 "Microsoft Word 2007+" 则可直接用 python-docx
```

## 适用场景
- 格式要求文件是旧 .doc 时
- 任何历史文档遇到 python-docx 报错的情况
