# 架构师开源情报站

一个自部署的开源项目情报面板。

它会跟踪 GitHub Releases 和官方文档更新，只分析新增或变化内容，沉淀成中文结论、同步日志和日报首页。
对于 Furo / Sphinx 风格文档，现已支持首次完整解读、页面级 diff 更新解读和单页变更查看。

## 现在能做什么

- 监控项目的 release 和文档变化
- 对新增内容做中文分析
- 对 Furo / Sphinx 文档做首读解读和更新 diff 解读
- 首页展示固定日报
- 展示增量提醒和同步日志
- 按项目下钻查看结论
- 在“文档解读”页查看项目首读、文档事件流和单页 diff

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
PACKY_PROTOCOL=
PACKY_REASONING_EFFORT=
PACKY_DISABLE_RESPONSE_STORAGE=
OPENAI_API_KEY=
OPENAI_API_URL=
OPENAI_MODEL=
OPENAI_PROVIDER=
OPENAI_PROTOCOL=
GITHUB_TOKEN=
```

`PACKY_PROTOCOL` / `OPENAI_PROTOCOL` 只在网关路径不能从 URL 直接判断协议时需要显式设置。
例如 OpenAI 兼容网关走非标准路径时，可设置为 `openai-chat` 或 `openai-responses`。

运行时规则：

- `PACKY_*` 和 `OPENAI_*` 都会被后端读取；如果前端尚未显式保存“当前主供应商”，服务会自动优先选择已经配置好 API key 的那一套。
- `docker compose` 会把两套环境变量一起注入后端容器。
- 配置中心里的 AI 配置属于“二次覆盖层”：前端保存后优先使用保存值；字段留空时继续回退到容器环境变量。

## 测试

```bash
npm test
./.venv/bin/python3 -m pytest -q
```

## Docker / GHCR

本仓库提供前后端双镜像容器化方案：

- 后端镜像：`Dockerfile.backend`
- 前端镜像：`Dockerfile.frontend`
- 本地编排：`docker-compose.yml`
- GHCR 发布工作流：`.github/workflows/publish-ghcr.yml`

本地启动：

```bash
docker compose up --build
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`

前端容器会通过 Nginx 将 `/api/*` 代理到 `backend:8000`，因此 compose 下不需要单独改前端 API 地址。

后端数据默认持久化到 compose volume，并挂载到容器内的 `backend/data/`。

如果直接使用 GHCR 镜像，可在 `docker-compose.yml` 中将 `build` 改为对应镜像标签，例如：

```yaml
image: ghcr.io/<owner>/<repo>/backend:latest
image: ghcr.io/<owner>/<repo>/frontend:latest
```

## 本地容器 E2E 验证

仓库内置了针对 `Incus` Furo 文档站的本地容器 E2E 脚本：

```bash
export OPENAI_API_KEY=...
export OPENAI_API_URL=https://code.swpumc.cn
export OPENAI_MODEL=gpt-5.4
export OPENAI_PROTOCOL=responses

bash scripts/e2e_incus_container.sh
```

如果你已经使用 `PACKY_*` 作为主通道，也可以继续沿用原有变量名；脚本会同时识别两套环境变量。

如果你的网关明确支持 `reasoning_effort`，可以额外设置：

```bash
export PACKY_REASONING_EFFORT=high
```

默认验证样本：

- GitHub：`https://github.com/lxc/incus`
- Docs：`https://linuxcontainers.org/incus/docs/main/`

脚本会：

- 使用隔离端口和隔离 compose project 启动前后端容器
- 预置空数据目录，避免 seed 项目干扰 E2E
- 创建 `Incus` 项目并仅启用文档区
- 触发真实同步并等待首读分析完成
- 验证 docs API 返回 `initial_read`
- 用 Playwright 打开“文档解读”页并截图

默认不会自动销毁容器，便于排查；需要清理时使用：

```bash
bash scripts/e2e_incus_container.sh --cleanup
```
