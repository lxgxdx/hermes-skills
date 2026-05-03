# GitHub 搜索替代方案

当 GitHub 搜索 API 和 `gh` CLI 都不可用时，用以下替代：

## 1. SourceGraph（无需登录）

全网代码搜索，覆盖 GitHub、GitLab、Bitbucket：
```
https://sourcegraph.com/search?q=刹车片钢背+language:Chinese&patternType=standard
```

## 2. GitHub 中文搜索（无需账号）

专门针对中文项目的搜索：
```
https://github.com/search?q=%E5%88%86%E8%BD%A6%E7%89%87%E9%92%A2%E8%83%8C&type=code
```

## 3. Google / Bing（无需认证）

搜索 GitHub 仓库内的内容：
```
site:github.com "刹车片钢背"
site:github.com "冲压光亮带"
```

## 4. 关键词组合

中文技术词在 GitHub 上较罕见，可尝试：
- 英文：`brake pad steel back`、`stamped bright band`
- 行业词：`摩擦材料`、`制动片`

## 5. 在具体仓库内搜索

如果知道大概的公司/厂商，用：
```
https://github.com/<org>/<repo>/search?q=steel+brake+pad
```
