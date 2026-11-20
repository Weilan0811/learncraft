你负责修复学习内容大纲。只返回符合要求的完整JSON大纲。

学生请求与生成参数：
{request_json}

原大纲：
{outline_json}

本次校验问题：
{errors_json}

实际可用资料（这是全部可引用的片段）：
{retrieval_results}

修复要求：
- 保持学习目标和内容类型；只对需要修复的部分调整，遵守章节数量限制。
- 每章给出可独立执行、非空的知识查询；引用只能使用上述实际片段编号。
- 不为了通过校验给章节填写不相关的编号，不将教学加工或大纲本身作为外部知识依据。
- 如果资料确实不足以支持章节，将缺少的知识列入metadata.insufficient_knowledge，保留清楚的原因，不编造引用。
- 确实能够依据资料完成修复时，清除原有metadata.insufficient_knowledge。
