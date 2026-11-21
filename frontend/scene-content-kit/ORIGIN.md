# 来源与许可证

`scene-content-kit` 基于 [THU-MAIC/OpenMAIC](https://github.com/THU-MAIC/OpenMAIC) 的幻灯片数据结构和静态渲染实现改编，经过简化和封装。

## 许可依据

组件采用 MIT，保留 `Copyright (c) 2026 THU-MAIC` 及[上游许可证原文](LICENSE.OpenMAIC)。本地添加和修改部分适用项目[根 MIT 许可证](../../LICENSE)。

代码及许可核对版本为 [`beac93ab3d81d71e902a631c2870f73383600279`](https://github.com/THU-MAIC/OpenMAIC/tree/beac93ab3d81d71e902a631c2870f73383600279)，核对日期为 2026-11-21。该版本的[项目根许可证](https://github.com/THU-MAIC/OpenMAIC/blob/beac93ab3d81d71e902a631c2870f73383600279/LICENSE)、[数据定义包许可证](https://github.com/THU-MAIC/OpenMAIC/blob/beac93ab3d81d71e902a631c2870f73383600279/packages/@maic/dsl/LICENSE)和[渲染包许可证](https://github.com/THU-MAIC/OpenMAIC/blob/beac93ab3d81d71e902a631c2870f73383600279/packages/@maic/renderer/LICENSE)均为 MIT，原文一致。

## 代码对应与改动

- `src/types.ts`：对应上游[幻灯片类型](https://github.com/THU-MAIC/OpenMAIC/blob/beac93ab3d81d71e902a631c2870f73383600279/packages/@maic/dsl/src/slides.ts)与[场景类型](https://github.com/THU-MAIC/OpenMAIC/blob/beac93ab3d81d71e902a631c2870f73383600279/packages/@maic/dsl/src/stage.ts)，保留场景、画布、主题、背景及基本元素结构，并删减和调整字段。
- `src/components/`：对应上游[场景入口](https://github.com/THU-MAIC/OpenMAIC/blob/beac93ab3d81d71e902a631c2870f73383600279/components/stage/scene-renderer.tsx)、[画布](https://github.com/THU-MAIC/OpenMAIC/blob/beac93ab3d81d71e902a631c2870f73383600279/packages/@maic/renderer/src/SlideCanvas.tsx)及[元素渲染](https://github.com/THU-MAIC/OpenMAIC/blob/beac93ab3d81d71e902a631c2870f73383600279/packages/@maic/renderer/src/SlideElement.tsx)相关实现，本地仅提供文本、图片、基本形状、直线和表格的静态展示。
- `src/adapters/`、`src/factories/`、`index.ts`、样式、说明和 JSON 示例用于本地封装及使用。

此核对版本用于记录保留内容的 MIT 来源依据；最初提取时的上游提交没有记录。本目录未包含上游字体、媒体、编辑器及单独许可的第三方包。组件的数据格式以本地说明为准。
