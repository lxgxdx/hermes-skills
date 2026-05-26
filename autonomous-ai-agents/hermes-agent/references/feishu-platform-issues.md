# Feishu Platform — Known Issues

## open_id cross app (99992361)

**Error:**
```json
{"code": 99992361, "msg": "open_id cross app", "error": {"message": "Refer to the documentation..."}}
```

**Symptom:** Feishu robot API calls (`/open-apis/im/v1/messages`) return HTTP 400 with this error when using `tenant_access_token`.

**Root cause:** The `tenant_access_token` is scoped to a specific Feishu app (`app_id`). The target user's `open_id` belongs to a different app — they are not a member of the app associated with the token being used.

**Diagnosis:**
```python
# Get token
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
{"app_id": "cli_a969394fa639dcc0", "app_secret": "..."}

# Send message fails with 99992361
POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id
{"receive_id": "oc_7c656031826c26b15f17d010097f3619", ...}
# → 400: open_id cross app
```

**This user's config:**
- App ID: `cli_a969394fa639dcc0`
- User open_id: `oc_7c656031826c26b15f17d010097f3619`
- Status: ❌ Has been failing for 22+ days across multiple cron sessions

**Solutions (in order of preference):**

1. **Add user to the app** — If the Feishu app is an internal tool, add the target user's open_id as a member of the app in Feishu admin console
2. **Use user_access_token instead** — `tenant_access_token` → `user_access_token` for sending to arbitrary users
3. **Create a dedicated bot app** — Create a new Feishu app that is installed by and scoped to the target user
4. **Use receive_id_type=union_id** — If the user has a union ID that crosses app boundaries (enterprise Feishu only), try `union_id` instead of `open_id`

**Impact:** All Feishu webhook notifications (cron job completion, Dream Cycle reports, user model reports) fail silently for this user.

**Tracking:** This issue appears in 22+ consecutive cron sessions (2026-05-02 through 2026-05-27) with the same error pattern.
