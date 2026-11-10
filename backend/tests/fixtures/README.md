`podcast_speech.wav` 截取自项目真实播客任务 `task_ba2caf388555` 第一段语音的前一秒，由百炼 TTS 生成。用于验证 ffmpeg 的实际音频合成和恢复，不需要调用外部 API。

`interactive_learning_snapshot.json` 截取自真实互动讲义任务 `task_50d8ee6ad2ac`，保留原始请求、首个章节的规格与渲染产物，以及数据库实际保存的 `final_render` 外层结构。用于验证历史请求恢复和学习上下文读取，不需要调用外部 API。
