# 中文运维变化面板

这是一个“中文结论优先”的运维监控面板。

它不再直接展示英文 commits / releases / issues 列表，而是通过一个轻量 Python 后端：

- 支持项目配置后台，新增项目时填写 `GitHub URL + 官方文档 URL`
- 定时抓取 GitHub releases 和真实文档页面 / feed
- 只对新增或内容变化的事件调用大模型
- 把中文分析结果持久化到本地 JSON
- 保留已经固定的历史结论
- 前端打开时直接展示中文总结、详细说明、影响范围和建议动作

## 当前架构

- 前端：React + Vite + Tailwind CSS
- 后端：Flask + APScheduler
- 本地持久化：JSON 文件
- 测试：pytest + Vitest + Testing Library

## 核心流程

1. 后端启动时读取项目注册表。
2. 后台立即执行一次同步，并按配置间隔持续同步。
3. 上游事件会被归一化为稳定事件 ID。
4. 官方文档 / 官方博客类 feed 可以继续展开对应页面正文，再送入分析。
5. 只有新事件或内容发生变化的旧事件才会重新进入大模型分析。
6. 单条事件分析失败不会中断整轮同步。
7. 中文分析结果保存到 `backend/data/*.json`。
8. 前端通过 `/api/dashboard` 直接读取整理好的中文结论与项目源摘要。
9. 后台通过 `/api/projects` 和 `/api/projects/<id>/crawl-profile` 管理项目和抓取配置。

## 当前默认项目

- `OpenClaw`
  - GitHub: `https://github.com/openclaw/openclaw`
  - 文档区：关闭
- `Kubernetes`
  - GitHub: `https://github.com/kubernetes/kubernetes`
  - 文档: `https://kubernetes.io/zh-cn/docs/home/`

## 环境变量

复制 `.env.example` 到本地 `.env` 后填写：

```bash
PACKY_API_KEY=...
PACKY_API_URL=https://www.packyapi.com/v1/messages
PACKY_MODEL=claude-sonnet-4-6
GITHUB_TOKEN=
```

说明：

- `PACKY_API_KEY` 只用于后端，不会暴露到前端。
- `GITHUB_TOKEN` 是可选项，用于提高 GitHub API 速率限制额度。

## 启动方式

安装依赖：

```bash
npm install
python3 -m pip install -r requirements.txt
```

启动后端：

```bash
npm run dev:backend
```

启动前端：

```bash
npm run dev
```

前端默认地址：

```text
http://localhost:5173
```

后端默认地址：

```text
http://localhost:8000
```

桌面快捷开关：

- 已创建桌面文件 `启动 Intel Workbench.command`
- 已创建桌面文件 `停止 Intel Workbench.command`

也可以在项目目录手动执行：

```bash
bash scripts/start_intel_workbench.sh
bash scripts/stop_intel_workbench.sh
```

启动脚本会：

- 后台启动 Flask 后端
- 后台启动 Vite 前端
- 自动打开浏览器到 `http://127.0.0.1:5173`
- 将日志写到 `logs/backend.log` 和 `logs/frontend.log`

## 测试

后端测试：

```bash
python3 -m pytest backend/tests -q
```

前端测试：

```bash
npm test
```

## 数据文件

后端运行后会在 `backend/data` 下生成：

- `config.json`
- `projects.json`
- `crawl_profiles.json`
- `events.json`
- `analyses.json`
- `state.json`

这些文件是本地运行缓存，不需要提交。
