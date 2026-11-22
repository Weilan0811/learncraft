# LearnCraft 完整作品示例

这里保存四份实际生成的作品及必要资源，不需要 API Key。GitHub 文件页显示 HTML 源码；下载仓库 ZIP 并解压，打开 `docs/examples/index.html` 即可浏览。也可以下载对应目录的全部文件后本地打开。

| 作品 | 文件 | 来源 |
| --- | --- | --- |
| 交互讲义 | [打开文件](interactive-lesson/index.html)，需保留同目录 `runtime.js` | 历史任务 `task_47068de7b05d`，六章讲义 |
| 图文讲义 | [HTML 文件](lecture/index.html) | 任务 `task_3ec82e18c10f`，咖啡供需四章 |
| 图文推文 | [HTML 文件](social-post/index.html)，需保留 `assets/` | 历史任务 `task_641b951b25c1` |
| 播客 | [试听文件](podcast/index.html)、[音频](podcast/ai-life-and-work.mp3)、[文稿](podcast/transcript.md) | 历史任务 `task_05583827d29d` |

交互讲义复用原始章节 HTML/CSS 和题目，静态页面提供章节切换、单选反馈及简答参考要点。练习状态仅在当前页面保留，刷新后清除，不调用后台或模型。原项目的学习统计、复习生成及带历史作答的离线导出需要运行完整工作台。

讲义图片保持原始嵌入形式；推文只调整资源地址并补充独立 HTML 外壳；播客由原始完整 WAV 压缩为 MP3，未改变文稿或发言内容。示例为生成效果展示，内容可能存在概念简化，使用前请结合具体学习目的核查。

## 静态网站维护

仓库提供手动触发的 Pages 工作流，仅发布本目录。维护者在确认公开范围后，将 GitHub Pages 来源设为 GitHub Actions，再手动执行工作流；在线地址以部署成功返回值为准。离线文件始终可以使用。
