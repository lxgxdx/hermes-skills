# 统战品牌项目 — 2026-05-28 Brain 录入

来源：2026-05-27 cron session 实体提取。

## 已在 Brain 的页面（+15 新增）

### 品牌项目（10个）
| slug | 名称 | 类型 |
|------|------|------|
| `projects/wenhua-dapengche` | 文化大篷车 | project |
| `projects/lvse-zhitongche` | 绿色直通车 | project |
| `projects/lianqi-lianqi` | 莲企·廉企 | project |
| `projects/lianqing-qinglian` | 莲青擎莲 | project |
| `projects/shiquan-shimei` | 石全石美 | project |
| `projects/ta-ailian` | 她·爱莲 | project |
| `projects/yihui-yipin` | 一会一品 | project |
| `projects/baiming-zhuanjia` | 百名专家联百企 | project |
| `projects/mulan-hui` | 木兰荟·企业行 | project |
| `projects/qingqing-huiketing` | 亲清会客厅 | project |

### 组织/企业（3个）
| slug | 名称 | 类型 |
|------|------|------|
| `organizations/biguizhuyuan` | 碧桂园 | company |
| `organizations/wuzheng-jituan` | 五征集团 | company |
| `organizations/wulian-zhonghua-zhiyezhilianshe` | 县中华职业教育社 | organization |

### 联系人（2个）
| slug | 名称 | 类型 |
|------|------|------|
| `people/li-guodong` | 李国东 | person |
| `people/zhang-xia` | 张霞 | person |

## Dream Cycle 防重复原则

**已有页面不要重建**。运行 Dream Cycle 前先 `gbrain list --limit 100` 检查现有 slug，避免重复创建同名页面。

slug 命名约定：
- 人物：`people/<拼音全名>` — 如 `people/li-guodong`
- 品牌：`projects/<拼音名>` — 如 `projects/wenhua-dapengche`
- 企业：`organizations/<拼音名>` — 如 `organizations/wuzheng-jituan`
