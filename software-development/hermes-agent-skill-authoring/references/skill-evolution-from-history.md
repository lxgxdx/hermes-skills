# 从历史对话进化 Skills

当用户要求"根据历史对话优化某个skill"时，遵循以下工作流：

## 标准流程

### 第一步：读取当前 skill 全文
- `skill_view(name)` 获取完整内容
- 注意文件大小：超过50KB的技能通常存在结构性问题

### 第二步：搜索历史对话中的教训
- `session_search` 多组关键词搜索（不要只搜一组）
- 搜索示例：
  - skill名 + "教训" / "优化" / "改进"
  - skill名 + skill名（同义词）
  - skill的核心主题 + core element关键词
  - skill中提到的具体功能名

### 第三步：分析教训归类
识别以下类型的改进点：
1. **用户纠正的工作流** → 编码为显式步骤或陷阱
2. **用户偏好** → 嵌入SKILL.md正文（不是仅存memory）
3. **失效的网站/工具** → 更新备用方案
4. **文件/API调用失败模式** → 增加验证步骤
5. **信息不对称** → 增加查询"已写内容"等上下文检查步骤

### 第四步：生成改进点子
不直接改全文，而是针对每个改进点用 `patch` 做精准替换。避免重写全文破坏原有结构。

### 第五步：记录进化过程
- 写 `references/YYYY-MM-DD-evolution-notes.md`
- 注明每个改进点的教训来源
- 列出后续优化建议（结构性问题等）

## 注意事项

- self-evolution 工具已被验证**只优化调用方式不改内容**，内容优化必须手动
- 纯proc step-by-step内容比length短，关键improvement在preference/fallback/validation
- 用户给出的体验feedback是最重要的改进信号
