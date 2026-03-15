# 架构师开源情报站

一个自部署的开源项目情报面板。

它会跟踪 GitHub Releases 和官方文档更新，只分析新增或变化内容，沉淀成中文结论、同步日志和日报首页。

当前版本重点是三件事：

- 增量同步开源项目的 release 和文档变化
- 把新增变化整理成中文结论、日报和日志
- 提供一个 `live-only` 的 AI 研究助手，围绕公网信息和已同步证据输出 Markdown 研究报告

## 现在能做什么

- 监控项目的 release 和文档变化
- 对新增内容做中文分析
- 首页展示固定日报
- 展示增量提醒和同步日志
- 按项目下钻查看结论
- AI 控制台支持研究型问答和证据链展示

## 架构

![系统架构](docs/assets/architecture-overview.svg)

## 截图

![日报首页](docs/assets/screenshot-home.png)

![同步监控](docs/assets/screenshot-sync-monitor.png)

![情报监控](docs/assets/screenshot-project-monitor.png)

## 启动

```bash
npm install
python3 -m pip install -r requirements.txt
./scripts/start_intel_workbench.sh
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`

停止：

```bash
./scripts/stop_intel_workbench.sh
```

## 环境变量

至少配置这些：

```bash
PACKY_API_KEY=...
PACKY_API_URL=https://www.packyapi.com/v1/messages
PACKY_MODEL=claude-opus-4-6
GITHUB_TOKEN=
```

可选：

```bash
LLM_FALLBACK_API_KEY=...
LLM_FALLBACK_API_URL=https://www.packyapi.com/v1/messages
LLM_FALLBACK_MODEL=glm-5
```

## 当前现状

- 首页以固定日报为主，增量变化和同步状态分开展示
- 情报监控支持按项目、技术分类、关注主题筛选
- AI 控制台默认只走 `live`，并优先保证相关性，避免无关项目混入
- 如果公网抓取失败，AI 控制台会优先回退到同项目的本地已同步证据
- 如果某个项目本地还没有同步到事件，AI 控制台也无法给出高质量结论

## 测试

```bash
npm test
.venv/bin/python -m pytest -q
```
