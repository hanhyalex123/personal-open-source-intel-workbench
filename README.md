# 架构师开源情报站

一个自部署的开源项目情报面板。

它会跟踪 GitHub Releases 和官方文档更新，只分析新增或变化内容，沉淀成中文结论、同步日志和日报首页。

## 现在能做什么

- 监控项目的 release 和文档变化
- 对新增内容做中文分析
- 首页展示固定日报
- 展示增量提醒和同步日志
- 按项目下钻查看结论

## 界面

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

## 测试

```bash
npm test
.venv/bin/python -m pytest -q
```
