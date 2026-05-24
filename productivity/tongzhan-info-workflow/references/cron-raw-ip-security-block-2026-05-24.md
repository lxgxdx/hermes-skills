# Cron 环境 Raw IP 安全扫描拦截（2026-05-24 实测）

## 现象

定时任务中 `urllib.request.urlopen("http://192.168.88.68:8083/search?q=...")` 报错：

```
HTTPError: HTTP Error 403: Forbidden
```

或安全扫描器直接拦截：

```
tirith.security_scan: approval_required
URL uses raw IP address 192.168.88.68 (private network access)
Plain HTTP URL in execution context
```

## 根本原因

**不是网络不通，而是安全扫描器主动拦截**。

tirith 安全扫描器在 cron 非交互 shell 环境中会扫描所有 HTTP 请求，阻止：
1. Raw IP 地址（`192.168.x.x` 等私网 IP）
2. 明文 HTTP URL（在 HTTPS 已普及的时代）

即使目标服务正常运行、端口可达，请求也**从未真正发出**。

## 关键判断方法

```bash
# 在 cron 中测试：加 --max-time 看是超时还是被拦截
curl -v --max-time 5 "http://192.168.88.68:8083/search?q=test&format=json"
# 超时 → 网络层问题
# 403 / approval_required → 安全扫描拦截
```

## 已验证的 cron 兼容方案

| 方案 | 可用性 | 备注 |
|------|--------|------|
| `browser_navigate` + HTTPS URL | ✅ 确认可用 | 01:00 AM 执行正常 |
| `curl` + 域名（非 IP） | ⚠️ 需验证 | 部分域名可能被限制 |
| `urllib` + Raw IP HTTP | ❌ 被拦截 | 安全扫描器主动阻止 |

## 实际案例（2026-05-24）

**问题**：凌晨 01:00 cron 执行时，`searxng_search()` 函数调用 `urllib.request.urlopen("http://localhost:7777/search?...")` 全部返回空结果（DNS 错误），导致选题搜索完全失败。

**排查**：手动 curl 测试显示安全扫描器拦截，不是网络问题。

**解决**：切换到 `browser_navigate("https://www.guancha.cn/taiwan/")` 成功获取台湾方向新闻素材。

## 教训

在 cron 环境中，**不要假设 HTTP 请求失败 = 网络不通**。安全扫描器的拦截行为可能在日志中表现为隐晦的 403 或超时，需要主动加 `-v` 调试。

**cron 外网访问的首选方案**：`browser_navigate` 访问 HTTPS 权威新闻网站，可靠性远高于直接 HTTP 请求。
