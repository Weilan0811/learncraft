# 自托管知识库

知识库为内容生成提供可检索的自有材料。引擎位于 `knowledge/engine/`，后端适配器位于 `backend/app/services/local_kb_service.py`。它可以独立使用，也可以接入内容生成任务。

本说明的命令从仓库根目录执行。原始材料、索引和本地模型均不进入 Git。

## 添加第一份材料

先安装基础依赖，再复制仓库自行编写的示例：

```powershell
uv sync --group dev
New-Item -ItemType Directory -Force knowledge/raw
Copy-Item knowledge/examples/workbench-guide.md knowledge/raw/workbench-guide.md
uv run python -m knowledge.scripts.query "如何重试失败的资源" --method keyword
```

最后一条命令使用真实中文分词和 BM25，不需要向量模型或外部 API。macOS、Linux 可用 `mkdir -p` 和 `cp` 完成相同复制操作。

自有材料使用 UTF-8 Markdown，文件名作为文档编号，头部使用简单的平面字段：

```markdown
---
title: 文档标题
topic: 主题
source_url: 可选的来源地址
---

## 小节标题

正文内容。
```

填写 `title` 和 `topic`，正文需要足够构成可检索片段。只收录有权使用的材料。嵌套 YAML 等复杂头部格式不在当前格式范围内。

## 配置向量模型

向量检索支持百炼云端向量服务和本地 BGE-M3，两者使用独立集合，避免混用向量空间。

云端方式无需下载本地模型。先在当前 PowerShell 终端设置：

```powershell
$env:KB_EMBEDDER = "bailian"
$env:CONTENT_GENERATOR_BAILIAN_API_KEY = "填写你的百炼Key"
```

本地方式需要额外依赖和模型文件：

```powershell
uv sync --extra kb-local --group dev
```

将 BAAI/bge-m3 模型放入仓库根目录 `.models/bge-m3`，或用系统环境变量 `BGE_M3_PATH` 指定已有模型目录。该目录应包含模型配置和权重。设置 `KB_EMBEDDER=bge_m3` 后使用本地模型；不设置时默认选择它。模型权重需自行取得，仓库不分发权重。

独立命令读取系统环境变量。后端会从 `.env` 读取百炼 Key 并传给检索适配器；`KB_EMBEDDER`、`BGE_M3_PATH` 和 `KB_FILTER_JUNK` 仍应设置在启动进程的系统环境中。

## 建库和查询

```powershell
uv run python -m knowledge.scripts.build_kb --rebuild
uv run python -m knowledge.scripts.query "如何重试失败的资源" --method router
```

可选检索方式为 `keyword`（关键词）、`vector`（向量）、`hybrid`（等权排名融合）和 `router`（按查询类型加权融合）。除关键词方式外，查询前应先建立当前向量模型的索引。

缓存写入 `storage/kb/`，向量写入 `storage/qdrant_kb/`。修改原始文件后，使用下方导入命令同步；大量调整材料或切分配置时使用 `--rebuild` 重建。运行建库或增删命令前，停止正在读取同一索引的后端服务：Qdrant 本地目录由单个进程打开。

## 新增、替换和撤回

```powershell
uv run python -m knowledge.scripts.ingest --file knowledge/raw/workbench-guide.md
uv run python -m knowledge.scripts.ingest --retract workbench-guide
```

同名文件再次导入会替换该文档的向量，不追加旧版本。撤回编号使用文件名去掉 `.md` 后的部分；原始文件移动到 `storage/kb/retracted/`，并从检索索引移除。恢复时将文件重新导入。

不要手动删除向量目录中的单个文件。原始材料是可恢复来源，索引是可重建数据。

## 接入内容生成

在 `.env` 设置 `CONTENT_GENERATOR_KB_PROVIDER=local`，选择好系统环境中的向量模型，重启后端。默认不开启知识库。

| 请求字段 | 行为 |
|---|---|
| `kb_mode=platform` | 检索平台材料，默认模式 |
| `kb_mode=materials_only` | 只检索本次请求的附件，无需平台材料 |
| `kb_mode=fused` | 分别检索平台与附件，再融合排名 |

附件通过 `attachments: [{filename, content}]` 传入，最多 10 份，每份正文最多 200,000 个字符。只提供文件路径不会自动上传正文。初始化或检索失败会返回失败状态，生成任务可据此展示未使用知识库的原因。

已有 `knowledge_base_ids` 字段尚未提供按库分区的访问控制；当前本地平台库由服务配置决定。不要将其当成多用户权限隔离接口。

## 排查问题

- **没有片段**：检查正文长度、查询措辞和材料是否已同步；默认排除目录、参考文献和明显提取残留。`KB_FILTER_JUNK=0` 可关闭过滤，改动后重建索引并重启后端。
- **缺少模型**：确认 BGE-M3 模型目录，或切换到百炼并配置 Key。
- **集合不存在**：先为当前向量模型建库。
- **目录被占用**：停止使用同一 Qdrant 本地目录的其它进程。
- **切换模型后结果异常**：检查所用模型及对应集合，重新执行建库。

设计依据见 [知识库设计](../docs/design/knowledge-base-design.md)。
