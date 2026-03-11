# Project Monitor Navigation Design

**Date:** 2026-03-10

## Goal

提升 `项目监控` 页的项目区分度，并增加类似 Kubernetes 文档的右侧跟随目录，让用户能够快速定位到某个项目、其 Release 区以及文档分类区。

## Problems

- 多个项目连续堆叠时，项目边界不够明显。
- `ReleaseNote 区` 和 `文档区` 都是卡片流，视觉层级相近，扫描成本高。
- 当项目增多时，用户需要滚动很长距离才能找到目标项目。

## Chosen Direction

采用“两层分隔 + 右侧目录”的方案：

- 首页与项目页统一引入项目级强调色，但只用于边线、浅底纹和标题强调。
- `项目监控` 页改成主内容区 + 右侧 sticky 导航。
- 右侧导航按 `项目 -> Release -> 文档分类` 组织。

## Reference Direction

- Kubernetes docs: 使用右侧目录降低长页面定位成本。
- Linear swimlanes: 使用分组和浅色边界增强列表扫描效率。

## UX Notes

- 目录只负责导航，不承载业务摘要。
- 桌面端右侧 sticky，移动端退化为普通块，不影响阅读。
- 当前浏览区域的项目在导航里高亮，形成“当前位置”反馈。
