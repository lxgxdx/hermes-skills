# Feishu API 消息发送 — 常见坑

## open_id vs chat_id（最常见错误）

发送 Feishu 消息时，`receive_id_type=open_id` 必须使用用户的 **open_id**，而不是 chat_id。

| ID类型 | 值 | 用途 |
|--------|---|------|
| **open_id** | `ou_ea6590a294ed18aab85697c5862e83b6` | ✅ 发送消息必须用这个 |
| **chat_id** | `oc_7c656031826c26b15f17d010097f3619` | ❌ 群聊/会话ID，不可用于发送 |
| **union_id** | `on_818426725f6ef8b6e0414d92e5d23e4f` | 跨应用用户标识 |

**错误信息**：`"open_id cross app"` — 表示 open_id 属于另一个 app，不能跨 app 使用。

## 获取 token 的标准代码

```python
import urllib.request, json

with open('/home/lxgxdx/.hermes/.env') as f:
    for line in f:
        if 'FEISHU_APP_SECRET' in line:
            app_secret = line.strip().split('=', 1)[1]
        if 'FEISHU_APP_ID' in line:
            app_id = line.strip().split('=', 1)[1]

req = urllib.request.Request(
    'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    data=json.dumps({'app_id': app_id, 'app_secret': app_secret}).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read())['tenant_access_token']
```

## 发送消息的标准代码

```python
send_req = urllib.request.Request(
    'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
    data=json.dumps({
        'receive_id': 'ou_ea6590a294ed18aab85697c5862e83b6',  # open_id
        'msg_type': 'text',
        'content': json.dumps({'text': '消息内容'})
    }).encode(),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    },
    method='POST'
)
with urllib.request.urlopen(send_req) as resp:
    result = json.loads(resp.read())
```

## cron 环境下飞书 Webhook 失效

hermes-gateway 的飞书 webhook 在 cron 环境下可能报 `"code":10001,"msg":"token invalid"`。这是因为 gateway 的飞书连接在 cron 独立进程中不存在。

**解决方案**：直接调用 Feishu REST API（如上），不依赖 gateway webhook。

## 查询用户 open_id

如果只知道用户的 chat_id 或其他标识，通过联系人 API 查询：

```python
search_req = urllib.request.Request(
    'https://open.feishu.cn/open-apis/contact/v3/users/batch?user_ids=ou_ea6590a294ed18aab85697c5862e83b6',
    headers={'Authorization': f'Bearer {token}'}
)
with urllib.request.urlopen(search_req) as resp:
    result = json.loads(resp.read())
    # result['data']['items'][0] 包含 union_id, open_id 等
```

## lxgxdx 的 ID 速查

| 字段 | 值 |
|------|---|
| open_id | `ou_ea6590a294ed18aab85697c5862e83b6` |
| chat_id | `oc_7c656031826c26b15f17d010097f3619` |
| union_id | `on_818426725f6ef8b6e0414d92e5d23e4f` |
