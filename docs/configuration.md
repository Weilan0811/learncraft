# LearnCraft 配置指南

本指南帮助你完成本地安装、选择模型服务，并按需要启用图片、语音与知识库。命令从仓库根目录执行；示例使用 PowerShell，macOS 和 Linux 可用 `cp` 完成文件复制。

## 1. 安装与基本运行

准备 Python 3.11+、uv、Node.js 22.12+ 和 npm。

```powershell
uv sync
if (!(Test-Path -LiteralPath .env)) {
    Copy-Item .env.example .env
}
```

`.env` 保存本地配置，修改后需要重启后端。先完成下节的文本服务配置，再启动：

```powershell
uv run python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

另开终端，从仓库根目录执行：

```powershell
cd frontend
npm ci
npm run dev
```

| 入口 | 默认地址 |
| --- | --- |
| 工作台 | http://127.0.0.1:5173 |
| 后端接口文档 | http://127.0.0.1:8000/docs |

首次启动会建立数据库并执行现有迁移。在前后端终端分别按 `Ctrl+C` 停止服务。

## 2. 先配置文本服务

将 `.env` 中的模式改为 `real`。示例文件默认的 `stub` 是开发占位模式，不会生成真实内容。

百炼配置：

```dotenv
CONTENT_GENERATOR_PROVIDER_MODE=real
CONTENT_GENERATOR_TEXT_PROVIDER=bailian
CONTENT_GENERATOR_TEXT_MODEL=qwen3.5-flash
CONTENT_GENERATOR_BAILIAN_API_KEY=填写你的百炼Key
```

使用 DeepSeek 时，替换对应字段：

```dotenv
CONTENT_GENERATOR_TEXT_PROVIDER=deepseek
CONTENT_GENERATOR_TEXT_MODEL=deepseek-v4-flash
CONTENT_GENERATOR_DEEPSEEK_API_KEY=填写你的DeepSeekKey
```

模型名需要与你的服务账户可调用的模型一致。全部环境变量及服务地址见根目录 `.env.example`；真实密钥只保存在本地 `.env` 中。

## 3. 各类内容需要哪些服务

| 内容 | 文本 | 图片 | 语音 |
| --- | --- | --- | --- |
| 交互讲义 | 需要 | 基本流程无需配置 | 无需配置 |
| 图文讲义、幻灯片、图文推文 | 需要 | 需要 | 无需配置 |
| 播客 | 需要 | 无需配置 | 需要 |

### 图片

默认图片供应商为 APIMart：

```dotenv
CONTENT_GENERATOR_IMAGE_PROVIDER=apimart
CONTENT_GENERATOR_IMAGE_MODEL=gpt-image-2
CONTENT_GENERATOR_IMAGE_RESOLUTION=1k
CONTENT_GENERATOR_APIMART_API_KEY=填写你的APIMartKey
```

也支持百炼图片服务。选择 `CONTENT_GENERATOR_IMAGE_PROVIDER=bailian` 时，填写相应可用图片模型，并使用 `CONTENT_GENERATOR_BAILIAN_API_KEY`。

### 播客语音

当前使用百炼语音服务：

```dotenv
CONTENT_GENERATOR_TTS_PROVIDER=bailian
CONTENT_GENERATOR_TTS_MODEL=qwen3-tts-flash
CONTENT_GENERATOR_BAILIAN_API_KEY=填写你的百炼Key
CONTENT_GENERATOR_TTS_PERSON1_VOICE=Ethan
CONTENT_GENERATOR_TTS_PERSON2_VOICE=Cherry
CONTENT_GENERATOR_TTS_OUTPUT_FORMAT=mp3
```

文本使用 DeepSeek 时，播客语音仍需要单独提供百炼密钥。完整音频通过 ffmpeg 编码合成，默认使用 `imageio-ffmpeg` 附带的程序；已有系统程序时，可用 `CONTENT_GENERATOR_FFMPEG_BINARY` 指定路径。

## 4. 可选知识库

默认关闭知识库，首次使用交互讲义无需建库。启用后，可使用自己的 UTF-8 Markdown 材料。

先验证关键词检索：

```powershell
New-Item -ItemType Directory -Force knowledge/raw
Copy-Item knowledge/examples/workbench-guide.md knowledge/raw/workbench-guide.md
uv run python -m knowledge.scripts.query "如何重试失败的资源" --method keyword
```

关键词检索不需要向量模型。完整混合检索还需要选择向量服务并建立索引。

**百炼向量服务：** 在建库和后端使用的终端中设置：

```powershell
$env:KB_EMBEDDER = "bailian"
$env:CONTENT_GENERATOR_BAILIAN_API_KEY = "填写你的百炼Key"
```

**本地 BGE-M3：** 安装可选依赖，并指定已有模型目录：

```powershell
uv sync --extra kb-local
$env:KB_EMBEDDER = "bge_m3"
$env:BGE_M3_PATH = "你的BGE-M3模型目录"
```

两种方式任选其一。设置后执行：

```powershell
uv run python -m knowledge.scripts.build_kb --rebuild
uv run python -m knowledge.scripts.query "如何重试失败的资源" --method router
```

再在 `.env` 中加入并重启后端：

```dotenv
CONTENT_GENERATOR_KB_PROVIDER=local
```

`KB_EMBEDDER`、`BGE_M3_PATH` 和 `KB_FILTER_JUNK` 通过启动进程的系统环境读取。独立建库命令也需要自己的凭据环境，不能只依赖后端读取 `.env`。

### 材料范围与更新

| 请求字段 | 检索范围 |
| --- | --- |
| `kb_mode=platform` | 平台知识库，默认模式 |
| `kb_mode=materials_only` | 当前请求的附件 |
| `kb_mode=fused` | 平台材料与附件分别检索后融合 |

附件通过 `attachments: [{filename, content}]` 提交正文，最多 10 份，每份最多 200,000 个字符。仅附件模式无需平台索引。`knowledge_base_ids` 尚未实现多用户库权限管理。

```powershell
uv run python -m knowledge.scripts.ingest --file knowledge/raw/workbench-guide.md
uv run python -m knowledge.scripts.ingest --retract workbench-guide
```

同名导入会替换该文档，撤回会移出索引并保留原文。建库或更新前，停止使用同一 Qdrant 本地目录的后端服务。材料格式、模型路径与维护命令详见[知识库使用说明](../knowledge/README.md)。

## 5. 数据、日志与调用成本

| 配置 | 默认值与用途 |
| --- | --- |
| `CONTENT_GENERATOR_DATABASE_URL` | `sqlite:///storage/tasks.db`，任务、学习事件与生成记录 |
| `CONTENT_GENERATOR_STORAGE_ROOT` | `storage`，产物与资源文件 |
| `CONTENT_GENERATOR_LOG_ROOT` | `storage/logs` |
| `CONTENT_GENERATOR_DEBUG_ROOT` | `storage/debug_workflow`，工作流调试快照 |

上述相对路径以仓库根目录为基准。备份时停止服务，保存数据库与关联资源文件；只保留数据库可能无法恢复图片、音频和导出内容。外部材料和索引也应按实际使用情况保存。

调用量取决于章节数、内容类型、重试和复习次数。启用本地知识库后，大纲前增加一次查询规划；云端向量、图片和语音分别产生对应服务费用。复习生成是一项新任务。

默认章节并发为 3、图片并发为 3、语音并发为 4，可通过 `.env.example` 中对应的并发字段调整。遇到服务商限流时先降低并发；提高并发不会减少总生成量。

## 6. 常见问题

| 现象 | 检查方法 |
| --- | --- |
| 页面正常，生成内容像固定示例 | 检查模式是否为 `real`，修改后重启后端 |
| 文本生成失败 | 检查所选供应商、模型名、密钥和账户额度 |
| 正文完成，部分图片或语音失败 | 查看对应资源错误，检查服务配置后单独重试 |
| 推文出现微信资源提示 | 本地预览使用本地资源；发布到微信还需要上传图片并取得微信资源编号，本地预览不等于发布完成 |
| 知识库没有结果 | 检查材料、向量模型、建库状态及检索记录中的空结果或失败原因 |
| Qdrant 目录被占用 | 停止其他读取同一索引目录的进程 |
| 重启后任务显示中断 | 已有预览会保留；整体任务不会自动从中断节点续跑 |

更多实现与接口阅读路径见[架构与开发指南](architecture.md)。
