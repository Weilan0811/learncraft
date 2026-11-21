# 第三方组件与许可

项目自行开发的代码采用 [MIT License（MIT 许可证）](LICENSE)。下列第三方组件保留各自的许可和署名；根许可证不替代这些条款。

## wechat-claw-skill

- 本地目录：`backend/app/skills/wechat-claw-skill/`。
- 上游：[th3ee9ine/wechat-claw-skill](https://github.com/th3ee9ine/wechat-claw-skill)，作者声明为 39Claw。
- 核对版本：[`566d36c3caa9509d202934544d0171235a069239`](https://github.com/th3ee9ine/wechat-claw-skill/tree/566d36c3caa9509d202934544d0171235a069239)。
- 核对日期：2026-11-21。原有 31 个文件（含脚本、模板、说明和图片）与该版本一致。
- 许可依据：上游根 [LICENSE](https://github.com/th3ee9ine/wechat-claw-skill/blob/566d36c3caa9509d202934544d0171235a069239/LICENSE)，Apache-2.0；本地保留[完整原文](backend/app/skills/wechat-claw-skill/LICENSE)。
- 上游 `SKILL.md` 同时标注 `license: MIT`，与根许可证存在差异。本项目保留上游原文件，以完整 Apache-2.0 条款处理该组件。本次仅在组件目录新增来源说明，未修改上游文件。
- 该核对版本未发现 `NOTICE` 文件。安装依赖及调用外部服务时，还需遵守相应依赖或服务条款。

## scene-content-kit / OpenMAIC

- 本地目录：`frontend/scene-content-kit/`，基于 [THU-MAIC/OpenMAIC](https://github.com/THU-MAIC/OpenMAIC) 的幻灯片数据结构和静态渲染实现改编，经过简化和封装。
- 代码及许可核对版本：[`beac93ab3d81d71e902a631c2870f73383600279`](https://github.com/THU-MAIC/OpenMAIC/tree/beac93ab3d81d71e902a631c2870f73383600279)。该版本的根项目、数据定义包 `@maic/dsl` 和渲染包 `@maic/renderer` 均明确采用 MIT。
- 保留 `Copyright (c) 2026 THU-MAIC` 及[许可原文](frontend/scene-content-kit/LICENSE.OpenMAIC)。本地组件声明 MIT，来源对应及改动见[来源说明](frontend/scene-content-kit/ORIGIN.md)。
- 未包含上游字体、媒体、编辑器及单独许可的第三方包。

## 安装依赖与模型

通过 uv 和 npm 安装的依赖保留各自的许可证，由依赖清单和锁定文件记录版本。本仓库不分发依赖目录、模型权重或本地实验语料；使用者下载模型和接入服务时，应查看相应模型或服务的条款。
